import json
import struct
import tempfile
import unittest
from pathlib import Path
from recovery import recover
from embedded import extract_asar, recover_sourcemap

def asar(path, files, body):
    raw = json.dumps({'files':files}).encode()
    padded = (len(raw)+3)&~3
    header = struct.pack('<II',4+padded,len(raw))+raw+b'\0'*(padded-len(raw))
    path.write_bytes(struct.pack('<II',4,len(header))+header+body)

class EmbeddedTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.p=Path(t.name)
    def test_asar_offline_and_map(self):
        source='export const x = 42;'
        m=json.dumps({'version':3,'sources':['webpack:///src/main.ts','missing.ts'],'sourcesContent':[source,None]}).encode()
        body=b'console.log(42)'+m
        f=self.p/'app.asar';asar(f,{'main.js':{'offset':'0','size':15},'main.js.map':{'offset':'15','size':len(m)}},body)
        r=recover(f,self.p/'out',emit=lambda _:None)
        self.assertEqual(len(r['source_maps']),1)
        item=r['source_maps'][0]
        self.assertEqual(item['missing'],['missing.ts'])
        p=self.p/'out'/item['output']/item['recovered'][0]['file']
        self.assertEqual(p.read_text(),source)
        self.assertEqual(len(list((self.p/'out'/'Source').rglob('main.js'))),1)
    def test_asar_bad_ranges(self):
        f=self.p/'a.asar';asar(f,{'file.js':{'offset':'2','size':100}},b'a')
        with self.assertRaises(ValueError):
            extract_asar(f,self.p/'out',{'files':0,'bytes':0},100,1000)
        self.assertFalse((self.p/'out').exists())
    def test_asar_traversal(self):
        f=self.p/'a.asar';asar(f,{'../outside':{'offset':'0','size':1}},b'a')
        with self.assertRaises(ValueError):
            extract_asar(f,self.p/'out',{'files':0,'bytes':0},100,1000)
    def test_map_does_not_follow_paths(self):
        f=self.p/'a.map';f.write_text(json.dumps({'version':3,'sources':['../../escape.ts','https://example.com/source.ts'],'sourcesContent':['source',None]}))
        result=recover_sourcemap(f,self.p/'out',{'files':0,'bytes':0},100,1000)
        self.assertEqual(result['missing'],['https://example.com/source.ts'])
        self.assertEqual((self.p/'out'/result['recovered'][0]['file']).read_text(),'source')
        self.assertFalse((self.p/'escape.ts').exists())
    def test_map_budget(self):
        f=self.p/'a.map';f.write_text(json.dumps({'version':3,'sources':['file.js'],'sourcesContent':['12345']}))
        with self.assertRaises(ValueError):
            recover_sourcemap(f,self.p/'out',{'files':0,'bytes':0},100,4)
