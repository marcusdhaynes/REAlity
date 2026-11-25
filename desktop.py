"""REAlity desktop interface."""
import queue, threading, tkinter as tk, webbrowser, sys
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from recovery import recover, locate, TOOLS

def main():
    root=tk.Tk();root.title('REAlity | Recovery Workbench');root.geometry('840x680');root.minsize(650,570)
    root.configure(bg='#100e19');style=ttk.Style(root);style.theme_use('clam')
    style.configure('.',background='#100e19',foreground='#eeeaf5',fieldbackground='#201a2d',font=('Segoe UI',10))
    style.configure('TButton',background='#32264a',foreground='#f1e7ff',padding=8);style.map('TButton',background=[('active','#594184'),('disabled','#282333')]);style.configure('TEntry',fieldbackground='#201a2d',foreground='#eeeaf5');style.configure('Title.TLabel',font=('Segoe UI',25,'bold'),foreground='#b79bff');style.configure('Sub.TLabel',foreground='#aaa1b9');style.configure('TCheckbutton',background='#100e19',foreground='#eeeaf5');style.map('TCheckbutton',background=[('active','#100e19')]);style.configure('Horizontal.TProgressbar',background='#a98af8',troughcolor='#241b36')
    frame=ttk.Frame(root,padding=24);frame.pack(fill='both',expand=True);frame.columnconfigure(0,weight=1);frame.rowconfigure(11,weight=1)
    ttk.Label(frame,text='REAlity',style='Title.TLabel').grid(row=0,column=0,sticky='w');ttk.Label(frame,text='LOCAL RECOVERY  /  PRESERVE · EXTRACT · ANALYZE',style='Sub.TLabel').grid(row=1,column=0,sticky='w',pady=(0,20))
    target=tk.StringVar();output=tk.StringVar(str(Path.home()/'Documents'/'REAlity-Recovered'));ext=tk.BooleanVar(False);status=tk.StringVar('Ready');q=queue.Queue();busy=False
    def pick(folder=False):
        p=filedialog.askdirectory() if folder else filedialog.askopenfilename()
        if p:target.set(p)
    def pickout():
        p=filedialog.askdirectory()
        if p:output.set(str(Path(p)/'REAlity-Recovered'))
    def row_at(i,var,buttons):
        r=ttk.Frame(frame);r.grid(row=i,column=0,sticky='ew',pady=(3,12));r.columnconfigure(0,weight=1);ttk.Entry(r,textvariable=var).grid(row=0,column=0,sticky='ew',padx=(0,8))
        for j,(label,cmd) in enumerate(buttons,1):ttk.Button(r,text=label,command=cmd).grid(row=0,column=j,padx=3)
    ttk.Label(frame,text='Original executable or installation folder').grid(row=2,column=0,sticky='w');row_at(3,target,[('File',lambda:pick()),('Folder',lambda:pick(True))]);ttk.Label(frame,text='New recovery workspace (must not exist)').grid(row=4,column=0,sticky='w');row_at(5,output,[('Choose Parent',pickout)])
    ttk.Checkbutton(frame,text='Run installed external analysis providers (explicit opt-in)',variable=ext).grid(row=6,column=0,sticky='w');ttk.Label(frame,text='Static mode does not run the original application or contact an AI provider.',style='Sub.TLabel').grid(row=7,column=0,sticky='w',pady=(5,8))
    bar=ttk.Frame(frame);bar.grid(row=8,column=0,sticky='ew',pady=8)
    def doctor():
        log.delete('1.0','end');log.insert('end','Installed provider detection (PATH):\n'+'\n'.join(f'{k}: {locate(k) or "not found"}' for k in TOOLS)+'\n')
    def start():
        nonlocal busy
        if busy:return
        a,b=target.get().strip(),output.get().strip()
        if not a or not b:messagebox.showerror('Missing path','Select an input and output.');return
        if Path(b).exists():messagebox.showerror('Output exists','Choose a new workspace.');return
        use=ext.get()
        if use and not messagebox.askyesno('External tools','Run locally installed analysis tools on preserved copies? Only use trusted tools and software you own.'):return
        busy=True;go.configure(state='disabled');progress.start(12);log.delete('1.0','end');status.set('Recovering…')
        def worker():
            try:recover(a,b,use,lambda s:q.put(('log',s)));q.put(('done','Inspection finished. See report for limitations.'))
            except Exception as e:q.put(('done','Partial or failed: '+str(e)))
        threading.Thread(target=worker,daemon=True).start()
    def tick():
        nonlocal busy
        while True:
            try:k,s=q.get_nowait()
            except queue.Empty:break
            log.insert('end',s+'\n');log.see('end')
            if k=='done':busy=False;progress.stop();go.configure(state='normal');status.set(s)
        root.after(100,tick)
    def openout():
        p=Path(output.get()).resolve()
        if p.is_dir():webbrowser.open(p.as_uri())
        else:messagebox.showinfo('Workspace','No workspace created yet.')
    def offline():
        html=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))/'REAlity-Offline.html'
        if html.is_file():webbrowser.open(html.as_uri())
        else:messagebox.showerror('Offline Inspector','Bundled inspector is missing.')
    def close():
        if busy:messagebox.showinfo('Recovery running','Wait for recovery to finish before closing.');return
        root.destroy()
    go=ttk.Button(bar,text='Begin Recovery',command=start);go.pack(side='left');ttk.Button(bar,text='Check Engines',command=doctor).pack(side='left',padx=5);ttk.Button(bar,text='Open Workspace',command=openout).pack(side='left',padx=5);ttk.Button(bar,text='Offline Inspector',command=offline).pack(side='left',padx=5);ttk.Button(bar,text='Craft Anything',command=lambda:webbrowser.open('https://github.com/storytold/craft-anything/releases/latest')).pack(side='left',padx=5)
    progress=ttk.Progressbar(frame,mode='indeterminate');progress.grid(row=9,column=0,sticky='ew',pady=6);ttk.Label(frame,textvariable=status,wraplength=720).grid(row=10,column=0,sticky='w',pady=5)
    log=tk.Text(frame,bg='#191424',fg='#d6c9eb',insertbackground='white',font=('Consolas',10),wrap='word',relief='flat',padx=10,pady=10);log.grid(row=11,column=0,sticky='nsew');log.insert('end','Select an EXE or the complete installation directory. All recovered files are kept in a separate workspace.\n');root.protocol('WM_DELETE_WINDOW',close);root.after(100,tick);root.mainloop()
if __name__=='__main__':main()
