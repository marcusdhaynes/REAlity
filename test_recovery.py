import io, tempfile, unittest, zipfile, struct
from pathlib import Path
from unittest.mock import patch
from recovery import recover, inspect, hashfile, safe_name

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name)
    def test_preservation(self):
        f=self.p/'a.exe';f.write_bytes(b'MZ' + b'a'*100);o=self.p/'out'
        recover(f,o,emit=lambda _:None)
        self.assertEqual(hashfile(f),hashfile(o/'Original/a.exe'))
    def test_classify(self):
        d=self.p/'src';d.mkdir();(d/'app.js').write_text('let x=1');(d/'a.png').write_bytes(b'png')
        o=self.p/'out';recover(d,o,emit=lambda _:None)
        self.assertTrue((o/'Source/Original/app.js').exists());self.assertTrue((o/'Assets/Original/a.png').exists())
    def test_nested(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('code.cs','class A {}')
        f=self.p/'a.zip'
        with zipfile.ZipFile(f,'w') as z:z.writestr('nested.zip',b.getvalue())
        o=self.p/'out';recover(f,o,emit=lambda _:None)
        self.assertEqual(len(list((o/'Source').rglob('code.cs'))),1)
    def test_traversal(self):
        f=self.p/'a.zip'
        with zipfile.ZipFile(f,'w') as z:z.writestr('../escape','bad')
        o=self.p/'out';r=recover(f,o,emit=lambda _:None)
        self.assertTrue(r['warnings']);self.assertFalse((self.p/'escape').exists())
    def test_windows_paths(self):
        for n in ['C:/a','a/CON.txt','a/../b','a\\..\\b','a.','/abs','x:stream']:
            with self.subTest(n=n),self.assertRaises(ValueError):safe_name(n)
    def test_pe_managed(self):
        b=bytearray(512);b[:2]=b'MZ';struct.pack_into('<I',b,60,64);b[64:68]=b'PE\0\0';struct.pack_into('<HH',b,68,0x8664,1);struct.pack_into('<H',b,84,240);struct.pack_into('<H',b,88,0x20b);struct.pack_into('<II',b,88+112+14*8,4096,72)
        f=self.p/'a.exe';f.write_bytes(b);r=inspect(f)
        self.assertEqual(r['architecture'],'x64');self.assertIn('managed CLR directory',r['markers'])
    def test_no_overwrite(self):
        f=self.p/'a';f.write_bytes(b'abc');o=self.p/'out';o.mkdir()
        with self.assertRaises(FileExistsError):recover(f,o)
    def test_no_external(self):
        f=self.p/'a.exe';f.write_bytes(b'MZ'+b'abc')
        with patch('recovery.run_tool') as call:
            recover(f,self.p/'out',emit=lambda _:None);call.assert_not_called()
if __name__=='__main__':unittest.main()
