"""ตัวจัดการข้อมูล local-only; แก้แล้วกดปุ่มจะเขียน JSON ทันที"""
import json
import re
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'image_metadata.json'; LOGOS=ROOT/'institution_logos.json'; SETTINGS=ROOT/'site_settings.json'; PUBLIC=ROOT/'public'
TYPE_VALUES=('มหาวิทยาลัย','วิทยาลัย','ทหาร/ตำรวจ','ไม่ระบุ')

class Manager:
    def __init__(self,root):
        self.root=root; self.records=[]; self.logos={}; self.settings={}; self.selected_index=None; self.selected_key=None; self.selected_logo=None
        root.title('BKW data manager'); root.geometry('1200x780'); root.minsize(850,560)
        ttk.Label(root,text='เลือกแถว → แก้ค่า → กด “แก้ไขและบันทึกทันที” ได้เลย ไม่ต้องกดซ้ำ | โลโก้แก้ในแท็บถัดไป',wraplength=1100).pack(fill='x',padx=12,pady=10)
        tabs=ttk.Notebook(root); tabs.pack(fill='both',expand=True,padx=10,pady=(0,10)); self.data_tab=ttk.Frame(tabs); self.logo_tab=ttk.Frame(tabs); tabs.add(self.data_tab,text='ข้อมูลรูปภาพ'); tabs.add(self.logo_tab,text='จัดการโลโก้')
        self.make_data_tab(); self.make_logo_tab(); self.load_all()

    def make_data_tab(self):
        t=self.data_tab; t.grid_columnconfigure(0,weight=1); t.grid_columnconfigure(1,weight=3); t.grid_rowconfigure(0,weight=1)
        self.record_list=tk.Listbox(t,width=52,exportselection=False); self.record_list.grid(row=0,column=0,sticky='nsew',padx=8,pady=8); self.record_list.bind('<<ListboxSelect>>',self.on_record_select)
        f=ttk.Frame(t); f.grid(row=0,column=1,sticky='nsew',padx=8,pady=8); f.grid_columnconfigure(1,weight=1)
        self.vars={}; fields=[('ปี','year','เช่น 2569'),('image URL / path','imageUrl','เช่น bkw2569/photo.jpg หรือ https://...'),('มหาวิทยาลัย/สถาบัน','institution','ชื่อสถาบันเต็ม'),('ประเภท','institutionType','เลือกหรือพิมพ์ค่า'),('คณะ','faculty','ไม่ต้องใส่สาขา'),('logo URL','logoUrl','URL โลโก้เฉพาะรูปนี้')]
        for row,(label,key,help_text) in enumerate(fields):
            ttk.Label(f,text=label).grid(row=row,column=0,sticky='nw',padx=(0,8),pady=7); var=tk.StringVar(); self.vars[key]=var
            if key=='institutionType': widget=ttk.Combobox(f,textvariable=var,values=TYPE_VALUES,state='normal')
            else: widget=ttk.Entry(f,textvariable=var)
            widget.grid(row=row,column=1,sticky='ew',pady=7); ttk.Label(f,text=help_text,foreground='#64748b').grid(row=row,column=2,sticky='nw',padx=8,pady=7)
        ttk.Button(f,text='เลือกไฟล์รูป',command=self.choose_file).grid(row=1,column=1,sticky='w')
        bar=ttk.Frame(f); bar.grid(row=7,column=0,columnspan=3,sticky='w',pady=18)
        ttk.Button(bar,text='เพิ่มรายการ',command=self.add_record).pack(side='left',padx=3); ttk.Button(bar,text='แก้ไขและบันทึกทันที',command=self.update_record).pack(side='left',padx=3); ttk.Button(bar,text='ลบ',command=self.delete_record).pack(side='left',padx=3); ttk.Button(bar,text='โหลดจากไฟล์ใหม่',command=self.load_records).pack(side='left',padx=3)

    def make_logo_tab(self):
        t=self.logo_tab; t.grid_columnconfigure(0,weight=1); t.grid_columnconfigure(1,weight=2); t.grid_rowconfigure(1,weight=1)
        ttk.Label(t,text='เลือกสถาบัน → แก้ URL โลโก้ → กด “แก้ไขและบันทึกโลโก้ทันที”  (ใส่ URL รูปโดยตรง เช่น https://site.com/logo.png)',wraplength=1050).grid(row=0,column=0,columnspan=2,sticky='ew',padx=10,pady=10)
        self.school_logo_var=tk.StringVar(); ttk.Label(t,text='โลโก้โรงเรียน (path หรือ URL)').grid(row=1,column=0,sticky='w',padx=10,pady=5); ttk.Entry(t,textvariable=self.school_logo_var).grid(row=1,column=1,sticky='ew',padx=10,pady=5); ttk.Button(t,text='บันทึกโลโก้โรงเรียน',command=self.save_school_logo).grid(row=1,column=1,sticky='e',padx=10,pady=5)
        self.instagram_var=tk.StringVar(); self.facebook_var=tk.StringVar()
        ttk.Label(t,text='Instagram URL').grid(row=2,column=0,sticky='w',padx=10,pady=5); ttk.Entry(t,textvariable=self.instagram_var).grid(row=2,column=1,sticky='ew',padx=10,pady=5)
        ttk.Label(t,text='Facebook URL').grid(row=3,column=0,sticky='w',padx=10,pady=5); ttk.Entry(t,textvariable=self.facebook_var).grid(row=3,column=1,sticky='ew',padx=10,pady=5)
        ttk.Button(t,text='บันทึกช่องทางติดต่อ',command=self.save_contact_links).grid(row=4,column=1,sticky='e',padx=10,pady=5)
        t.grid_rowconfigure(5,weight=1)
        self.logo_list=tk.Listbox(t,width=50,exportselection=False); self.logo_list.grid(row=5,column=0,sticky='nsew',padx=10,pady=8); self.logo_list.bind('<<ListboxSelect>>',self.on_logo_select)
        f=ttk.Frame(t); f.grid(row=5,column=1,sticky='new',padx=10,pady=8); f.grid_columnconfigure(1,weight=1); self.logo_name=tk.StringVar(); self.logo_url=tk.StringVar()
        ttk.Label(f,text='ชื่อสถาบัน').grid(row=0,column=0,sticky='w',padx=(0,8),pady=8); ttk.Entry(f,textvariable=self.logo_name).grid(row=0,column=1,sticky='ew',pady=8)
        ttk.Label(f,text='URL โลโก้').grid(row=1,column=0,sticky='w',padx=(0,8),pady=8); ttk.Entry(f,textvariable=self.logo_url).grid(row=1,column=1,sticky='ew',pady=8)
        bar=ttk.Frame(f); bar.grid(row=2,column=0,columnspan=2,sticky='w',pady=14); ttk.Button(bar,text='เพิ่มโลโก้',command=self.add_logo).pack(side='left',padx=3); ttk.Button(bar,text='แก้ไขและบันทึกโลโก้ทันที',command=self.update_logo).pack(side='left',padx=3); ttk.Button(bar,text='ลบโลโก้',command=self.delete_logo).pack(side='left',padx=3); ttk.Button(bar,text='โหลดใหม่',command=self.load_logos).pack(side='left',padx=3)

    def load_all(self): self.load_records(); self.load_logos(); self.load_settings()
    def load_settings(self):
        self.settings=json.loads(SETTINGS.read_text(encoding='utf-8')) if SETTINGS.exists() else {'bkwLogo':'/bkw_logo.png'}
        self.school_logo_var.set(self.settings.get('bkwLogo','/bkw_logo.png')); self.instagram_var.set(self.settings.get('instagram','https://instagram.com/phakin_bbx')); self.facebook_var.set(self.settings.get('facebook','https://facebook.com/PhakinCharatsri'))
    def save_school_logo(self):
        value=self.school_logo_var.get().strip() or '/bkw_logo.png'; self.settings['bkwLogo']=value; payload=json.dumps(self.settings,ensure_ascii=False,indent=2)+'\n'; SETTINGS.write_text(payload,encoding='utf-8'); PUBLIC.mkdir(exist_ok=True); (PUBLIC/'site_settings.json').write_text(payload,encoding='utf-8'); messagebox.showinfo('สำเร็จ','บันทึก path/URL โลโก้โรงเรียนแล้ว')
    def save_contact_links(self):
        self.settings['instagram']=self.instagram_var.get().strip(); self.settings['facebook']=self.facebook_var.get().strip(); payload=json.dumps(self.settings,ensure_ascii=False,indent=2)+'\n'; SETTINGS.write_text(payload,encoding='utf-8'); PUBLIC.mkdir(exist_ok=True); (PUBLIC/'site_settings.json').write_text(payload,encoding='utf-8'); messagebox.showinfo('สำเร็จ','บันทึก URL Instagram และ Facebook แล้ว')
    def load_records(self):
        # รักษาลำดับใน JSON เดิมไว้ เพื่อให้รายการใหม่ append ต่อท้ายจริง ๆ
        self.records=json.loads(DATA.read_text(encoding='utf-8')) if DATA.exists() else []; self.selected_index=None; self.selected_key=None; self.refresh_records()
    def sort_records(self):
        def key(record):
            path=str(record.get('path',record.get('imageUrl','')))
            number=int(re.search(r'_(\d+)(?:\.[^.]+)?$',path).group(1)) if re.search(r'_(\d+)(?:\.[^.]+)?$',path) else 0
            return (int(record.get('year',0) or 0), path.rsplit('/',1)[0], number, path)
        self.records.sort(key=key)

    def sort_records_by_year(self):
        """เรียงข้อมูลจากปีเก่าไปใหม่ โดยคงลำดับเดิมภายในปีเดียวกันไว้"""
        self.records.sort(key=lambda record: int(record.get('year', 0) or 0))
    def refresh_records(self):
        self.record_list.delete(0,tk.END)
        for i,r in enumerate(self.records): self.record_list.insert(tk.END,f'{i+1:03} | {r.get("year","")} | {r.get("institution","ไม่ระบุ")} | {r.get("faculty","ไม่ระบุ")}')
    def on_record_select(self,_=None):
        selected=self.record_list.curselection()
        if not selected:return
        self.selected_index=selected[0]; record=self.records[self.selected_index]; self.selected_key=self.record_key(record)
        for key,var in self.vars.items():var.set(record.get(key,record.get('path','') if key=='imageUrl' else ''))
    def choose_file(self):
        path=filedialog.askopenfilename(filetypes=[('Images','*.jpg *.jpeg *.png *.webp *.gif'),('All files','*.*')])
        if path:
            try:self.vars['imageUrl'].set(Path(path).relative_to(ROOT).as_posix())
            except ValueError:self.vars['imageUrl'].set(path)
    def form_record(self,old=None):
        new=dict(old or {}); new.update({key:var.get().strip() for key,var in self.vars.items()})
        try:new['year']=int(new.get('year') or 0)
        except ValueError:raise ValueError('ปีต้องเป็นตัวเลข เช่น 2569')
        if not 2500 <= new['year'] <= 2600: raise ValueError('กรุณาใส่ปี พ.ศ. ให้ถูกต้อง เช่น 2569')
        if not new.get('imageUrl') and not new.get('path'): raise ValueError('ต้องใส่ image URL / path ก่อนเพิ่มข้อมูล')
        if new.get('imageUrl') and not new.get('imageUrl','').startswith(('http://','https://')):new['path']=new['imageUrl']
        return new
    def record_key(self,record):
        return str(record.get('id') or record.get('path') or record.get('imageUrl') or '')
    def find_selected_index(self):
        if self.selected_key is None:return None
        for index,record in enumerate(self.records):
            if self.record_key(record)==self.selected_key:return index
        return None
    def write_records(self):
        payload=json.dumps(self.records,ensure_ascii=False,indent=2)+'\n'; backup_dir=ROOT/'admin_backups'; backup_dir.mkdir(exist_ok=True); stamp=datetime.now().strftime('%Y%m%d_%H%M%S'); (backup_dir/f'image_metadata_{stamp}.json').write_text(payload,encoding='utf-8'); DATA.write_text(payload,encoding='utf-8'); PUBLIC.mkdir(exist_ok=True); (PUBLIC/'image_metadata.json').write_text(payload,encoding='utf-8')
    def add_record(self):
        try:
            record=self.form_record()
            if any(self.record_key(old)==self.record_key(record) for old in self.records): raise ValueError('path/URL นี้มีอยู่แล้ว ระบบจะไม่เขียนทับรายการเดิม')
            # ให้ปีเก่าสุดอยู่ต้นไฟล์ และหมายเลขลำดับขยับตามตำแหน่งใหม่อัตโนมัติ
            self.records.append(record)
            self.sort_records_by_year()
            self.selected_key=self.record_key(record); self.write_records(); self.refresh_records(); self.selected_index=self.find_selected_index(); self.record_list.selection_set(self.selected_index); messagebox.showinfo('สำเร็จ','เพิ่มรายการใหม่และบันทึกแล้ว')
        except ValueError as e:messagebox.showerror('ข้อมูลไม่ถูกต้อง',str(e))
    def update_record(self):
        current=self.find_selected_index()
        if current is None:return messagebox.showwarning('ยังไม่ได้เลือก','คลิกเลือกรายการด้านซ้ายก่อน')
        try:
            updated=self.form_record(self.records[current]); duplicate=any(i!=current and self.record_key(old)==self.record_key(updated) for i,old in enumerate(self.records))
            if duplicate: raise ValueError('path/URL นี้มีอยู่แล้ว ระบบจะไม่เขียนทับรายการอื่น')
            self.records[current]=updated
            self.sort_records_by_year()
            self.selected_key=self.record_key(updated); self.write_records(); self.refresh_records(); self.selected_index=self.find_selected_index(); self.record_list.selection_set(self.selected_index); messagebox.showinfo('สำเร็จ','แก้ไขรายการเดิมและบันทึกลง image_metadata.json แล้ว')
        except ValueError as e:messagebox.showerror('ข้อมูลไม่ถูกต้อง',str(e))
    def delete_record(self):
        current=self.find_selected_index()
        if current is None:return messagebox.showwarning('ยังไม่ได้เลือก','คลิกเลือกรายการด้านซ้ายก่อน')
        if messagebox.askyesno('ยืนยัน','ลบรายการนี้หรือไม่'):self.records.pop(current); self.write_records(); self.selected_index=None; self.selected_key=None; self.refresh_records()

    def load_logos(self):
        self.logos=json.loads(LOGOS.read_text(encoding='utf-8')) if LOGOS.exists() else {}
        for r in self.records:
            name=r.get('institution','').strip()
            if name and name!='ไม่ระบุจากภาพ':self.logos.setdefault(name,'')
        self.selected_logo=None; self.refresh_logos()
    def refresh_logos(self):
        self.logo_list.delete(0,tk.END)
        for name in sorted(self.logos):self.logo_list.insert(tk.END,name)
    def on_logo_select(self,_=None):
        selected=self.logo_list.curselection()
        if not selected:return
        self.selected_logo=self.logo_list.get(selected[0]); self.logo_name.set(self.selected_logo); self.logo_url.set(self.logos.get(self.selected_logo,''))
    def write_logos(self):
        payload=json.dumps(self.logos,ensure_ascii=False,indent=2)+'\n'; LOGOS.write_text(payload,encoding='utf-8'); PUBLIC.mkdir(exist_ok=True); (PUBLIC/'institution_logos.json').write_text(payload,encoding='utf-8')
    def add_logo(self):
        name=self.logo_name.get().strip(); url=self.logo_url.get().strip()
        if not name:return messagebox.showerror('ข้อมูลไม่ครบ','ต้องใส่ชื่อสถาบัน')
        self.logos[name]=url; self.write_logos(); self.refresh_logos(); messagebox.showinfo('สำเร็จ','เพิ่มและบันทึกโลโก้แล้ว')
    def update_logo(self):
        name=self.logo_name.get().strip()
        if not name:return messagebox.showwarning('ยังไม่ได้เลือก','เลือกสถาบันหรือใส่ชื่อก่อน')
        self.logos[name]=self.logo_url.get().strip(); self.write_logos(); self.refresh_logos(); messagebox.showinfo('สำเร็จ','แก้ไขและบันทึกโลโก้ลง institution_logos.json แล้ว')
    def delete_logo(self):
        name=self.logo_name.get().strip()
        if name in self.logos and messagebox.askyesno('ยืนยัน','ลบโลโก้นี้หรือไม่'):self.logos.pop(name); self.write_logos(); self.refresh_logos()

if __name__=='__main__':
    root=tk.Tk(); Manager(root); root.mainloop()
