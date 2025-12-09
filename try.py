from kivymd.uix.selectioncontrol import MDSwitch
from connect_db import  create_table_attandace, create_table_store_date,create_table_student_info
from crud_in_database import insert_into_student_info, update_into_setting_theam, update_into_setting_auto, create_row_for_lacture,get_theme_form_setting,save_attandance_in_db,check_table
# from kaki.app import App
from kivymd.uix.backdrop.backdrop import MDBoxLayout
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.lang import Builder
from kivy.app import App
from kivymd.uix.label import MDLabel
from kivymd.uix.pickers.datepicker.datepicker import MDTextField
from kivymd.uix.transition import MDFadeSlideTransition
from kivy.uix.settings import text_type
from kivy.uix.recyclegridlayout import defaultdict
from kivymd.uix.bottomnavigation.bottomnavigation import MDScreen
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.snackbar import Snackbar
from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from kivy.clock import Clock
from kivymd.uix.boxlayout import BoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu

import cv2 as cv
from kivy.properties import ObjectProperty
import time as t
import os
# Lazy import DeepFace only when needed to speed app start
DeepFace = None
from datetime import datetime, time as dtime, timedelta


class Screen_mange(MDScreenManager):
    def login_re(self, user, pas):
        self.current = "main"
    def on_kv_post(self, base_widget):
        check_table()


class Imag1(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cap = cv.VideoCapture(0)
        # lower camera resolution to reduce CPU
        try:
            self.cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
        except:
            pass
        self.frame_rgb = None
        self.save_imag = None
        self.cap_live = None
        self.source = r"D:\SmartAttendanceSystem\Kivy_app\attendance\login_img.png"

    def video_(self):
        # lower UI update rate to ~15 FPS
        self.cap_live = Clock.schedule_interval(self.video_display, 1 / 15.0)

    def video_display(self, dt):
        ret, frame = self.cap.read()
        if ret:
            self.save_imag = frame
            frame = cv.flip(frame, 0)
            self.frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
            texture.blit_buffer(self.frame_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            self.texture = texture

    def save(self,name,roll,mobile_number):
        try:
            cv.imwrite(f"D:\\SmartAttendanceSystem\\Kivy_app\\attendance\\{roll.text}.jpg", self.save_imag)
            self.re_camara() 
            defult_img = cv.imread(r"C:\Users\heman\Pictures\Screenshots\Screenshot 2025-04-27 164516.png")
            defult_img = cv.flip(defult_img, 0)
            defult_img = cv.cvtColor(defult_img, cv.COLOR_BGR2RGB)
            texture = Texture.create(size=(defult_img.shape[1], defult_img.shape[0]), colorfmt='rgb')
            texture.blit_buffer(defult_img.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            self.texture = texture
        except Exception as e:
            print("error saving image", e)

        try:
            success, buffer = cv.imencode(".jpg", self.save_imag)
            binary_data = buffer.tobytes()
            insert_into_student_info(int(roll.text),name.text,mobile_number.text,binary_data)
        except Exception as e:
            print("error in save student info in database", e)
            
    def re_camara(self):
        if self.cap_live:
            self.cap_live.cancel()
        try:
            self.cap.release()
        except:
            pass
        self.source = r"D:\SmartAttendanceSystem\Kivy_app\attendance\login_img.png"


class Start_attandance(Image):
    current_lecture_key = StringProperty("")
    auto_running = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cap = cv.VideoCapture(0)
        try:
            self.cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
        except:
            pass
        self.cap_live = None
        self.save_imag = None
        self.frame_rgb = None
        self.present = set()
        # throttling and reuse
        self._last_infer = 0.0
        self._infer_interval = 0.7  # seconds between recognitions

    def _ensure_deepface(self):
        global DeepFace
        if DeepFace is None:
            from deepface import DeepFace as DF
            DeepFace = DF

    def video_(self):
        try:
            self.cap = cv.VideoCapture(0)
            self.cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
        except:
            pass
        try:
            self.present.clear()
            # lower UI update rate
            self.cap_live = Clock.schedule_interval(self.video_display, 1 / 12.0)
            self.auto_running = True
        except:
            pass

    def _recognize(self, frame):
        # resize to speed up search
        h, w = frame.shape[:2]
        scale = 0.6
        small = cv.resize(frame, (int(w*scale), int(h*scale)))
        try:
            self._ensure_deepface()
            re = DeepFace.find(
                img_path=small,
                db_path=r"D:\SmartAttendanceSystem\Kivy_app\attendance",
                model_name="SFace",
                detector_backend="opencv",
                enforce_detection=False
            )
            for df in re:
                if len(df) > 0:
                    top = df.iloc[0]
                    name = top["identity"].split("\\")[-1].split(".")[0]
                    self.present.add(name)
        except Exception as e:
            pass

    def video_display(self, dt):
        ret, frame = self.cap.read()
        if not ret:
            return
        # draw faces but skip heavy ops if none
        faces = []
        try:
            self._ensure_deepface()
            faces = DeepFace.extract_faces(
                img_path=frame,
                detector_backend="opencv",
                enforce_detection=False,
                align=True
            )
            for face in faces:
                box = face.get("facial_area", {})
                x, y, w, h = box.get("x",0), box.get("y",0), box.get("w",0), box.get("h",0)
                if w and h:
                    cv.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        except Exception:
            pass
        dis_img = cv.flip(frame, 0)
        self.frame_rgb = cv.cvtColor(dis_img, cv.COLOR_BGR2RGB)
        texture = Texture.create(size=(dis_img.shape[1], dis_img.shape[0]), colorfmt='rgb')
        texture.blit_buffer(self.frame_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
        self.texture = texture

        now = t.perf_counter()
        # Only run recognition when faces are present and interval elapsed
        if faces and (now - self._last_infer) >= self._infer_interval:
            self._last_infer = now
            self._recognize(frame)

    def re_camara(self):
        try:
            if self.cap_live:
                self.cap_live.cancel()
            self.cap.release() 
        except:
            pass
        self.auto_running = False
        try:
            if self.present:
                try:
                    save_attandance_in_db(self.present, self.current_lecture_key)
                except TypeError:
                    save_attandance_in_db(self.present)
            else:
                try:
                    save_attandance_in_db(set(), self.current_lecture_key)
                except TypeError:
                    pass
        except Exception as e:
            pass


class Setting(MDScreen):
    dynamic_input_box = ObjectProperty(None)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        self.s_h_x=.1
        self.s_h_y=.1
        self.lature_time=[]
        self.dynamic_input_pto=[]

    def time_manage(self, t):
        self.dynamic_input_box.clear_widgets()
        try:
            num = int(t)
        except ValueError:
            num = 1
        new_fild=[]
        for i in range(num):
            inner_layout=MDBoxLayout(orientation="horizontal",size_hint_y=None,size_hint_x=.5)
            str= MDTextField(hint_text=f"Lecture {i + 1}",mode="rectangle",size_hint_x=.15)
            new_fild.append(str)
            text_to=MDLabel(text=" to ",size_hint=(None,None),halign="center",valign="middle")
            end = MDTextField(hint_text=f"Lecture {i + 1}",mode="rectangle",size_hint_x=.15)
            new_fild.append(end)
            self.dynamic_input_pto.append(new_fild)
            self.lature_time.append((str, end))
            inner_layout.add_widget(str)
            inner_layout.add_widget(text_to)
            inner_layout.add_widget(end)
            self.dynamic_input_box.add_widget(inner_layout)
        button_lat=MDRaisedButton(text="Add Lecture",pos_hint={"x": 0.5},on_press=self.print_dynamic_input)
        self.dynamic_input_box.add_widget(button_lat) 

    def print_dynamic_input(self,dt):
        for i, (start_field, end_field) in enumerate(self.dynamic_input_pto):
            print(f"Lecture {i + 1}: {start_field.text} --> {end_field.text}")


class MyApp(MDApp):
    def build(self):  
        return Screen_mange()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auto = None  
        self.time_auto_man = []
        self.lacture_lay = BoxLayout()
        self.text_input = []
        self.LECTURE_WINDOWS = [
            ("L_1", dtime(13,30), dtime(14,0)),
            ("L_2", dtime(14,30), dtime(15,30)),
            ("L_3", dtime(16,30), dtime(17,0)),
            ("L_4", dtime(17,30), dtime(18,0)),
        ]
        self.attendance = None
        self._auto_tick = None
        self.manual_dialog = None

    def on_start(self):
        try:
            # access ids inside start_attandance screen
            start_screen = self.root.ids.main_screen_manager_home.get_screen('start_attandance')
            self.attendance = start_screen.ids.attendance if hasattr(start_screen.ids, 'attendance') else start_screen.ids.live_screen
            self._next_label = start_screen.ids.next_label if hasattr(start_screen.ids, 'next_label') else None
        except Exception:
            self.attendance = Start_attandance()
            self._next_label = None
        self._auto_tick = Clock.schedule_interval(self._auto_scheduler, 1)

    def _now(self):
        return datetime.now()

    def _within(self, start: dtime, end: dtime, nowt: dtime) -> bool:
        return start <= nowt <= end

    def _current_window(self):
        nowt = self._now().time()
        for key, s, e in self.LECTURE_WINDOWS:
            if self._within(s, e, nowt):
                return key, s, e
        return None

    def _next_window_info(self):
        now = self._now()
        today_windows = [(k, datetime.combine(now.date(), s), datetime.combine(now.date(), e)) for k,s,e in self.LECTURE_WINDOWS]
        future = [(k, s, e) for k,s,e in today_windows if e > now]
        if not future:
            return None
        # if within any, show time to end; else time to next start
        for k, s, e in future:
            if s <= now <= e:
                return (k, 'ends in', e - now)
        k, s, e = future[0]
        return (k, 'starts in', s - now if s > now else timedelta(0))

    def _auto_scheduler(self, dt):
        info = self._next_window_info()
        if self._next_label and info:
            k, word, delta = info
            mins = int(delta.total_seconds() // 60)
            secs = int(delta.total_seconds() % 60)
            self._next_label.text = f"{k} {word} {mins:02d}m {secs:02d}s"
        win = self._current_window()
        if win and not self.attendance.auto_running:
            key, s, e = win
            self.attendance.current_lecture_key = key
            Snackbar(text=f"Auto detect started for {key}").open()
            self.attendance.video_()
        if not win and self.attendance.auto_running:
            Snackbar(text="Auto detect stopped").open()
            self.attendance.re_camara()

    def theme_change(self, active):
        if active:
            self.theme_cls.theme_style = "Dark"
            update_into_setting_theam('Dark')
        else:
            self.theme_cls.theme_style = "Light"
            update_into_setting_theam('Light')
            
    def get_theme(self,switch):
        g_t= get_theme_form_setting()
        if g_t =="Dark":
            switch.active=True
            self.theme_cls.theme_style = "Dark"
            return True
        else:
            switch.active=False
            return False

    def auto_on_of(self, active):
        if active:
            if self.auto is None:
                pass
        else:
            if self.auto:
                self.auto.cancel()
                self.auto = None
            if self.attendance:
                self.attendance.re_camara()

    def open_manual_dialog(self):
        if self.manual_dialog:
            self.manual_dialog.dismiss()
        content = MDBoxLayout(orientation="vertical", spacing=12, padding=12)
        tf_rolls = MDTextField(hint_text="Roll numbers (comma-separated)")
        tf_lecture = MDTextField(hint_text="Lecture (1-4)")
        content.add_widget(tf_rolls)
        content.add_widget(tf_lecture)
        self.manual_dialog = MDDialog(
            title="Manual Attendance",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda *_: self.manual_dialog.dismiss()),
                MDRaisedButton(text="SAVE", on_release=lambda *_: self._save_manual(tf_rolls.text, tf_lecture.text))
            ]
        )
        self.manual_dialog.open()

    def open_edit_windows(self):
        # Dialog to edit lecture windows HH:MM-HH:MM lines per lecture
        box = MDBoxLayout(orientation='vertical', spacing=12, padding=12)
        fields = []
        for i,(k,s,e) in enumerate(self.LECTURE_WINDOWS, start=1):
            tf = MDTextField(hint_text=f"L_{i} (e.g., 13:30-14:00)", text=f"{s.strftime('%H:%M')}-{e.strftime('%H:%M')}")
            fields.append(tf)
            box.add_widget(tf)
        dlg = MDDialog(title="Edit Lecture Windows", type='custom', content_cls=box,
                       buttons=[MDFlatButton(text='CANCEL', on_release=lambda *_: dlg.dismiss()),
                                MDRaisedButton(text='SAVE', on_release=lambda *_: self._save_windows(dlg, fields))])
        dlg.open()

    def _save_windows(self, dlg, fields):
        new_windows = []
        try:
            for i, tf in enumerate(fields, start=1):
                val = tf.text.strip()
                start_s, end_s = val.split('-')
                sh, sm = map(int, start_s.split(':'))
                eh, em = map(int, end_s.split(':'))
                new_windows.append((f"L_{i}", dtime(sh,sm), dtime(eh,em)))
            self.LECTURE_WINDOWS = new_windows
            Snackbar(text="Lecture windows saved").open()
        except Exception:
            Snackbar(text="Invalid time format").open()
        finally:
            dlg.dismiss()

    def _save_manual(self, rolls_text: str, lec_text: str):
        if self.manual_dialog:
            self.manual_dialog.dismiss()
        try:
            rolls = [r.strip() for r in rolls_text.split(',') if r.strip()]
            key = f"L_{int(lec_text)}"
        except Exception:
            Snackbar(text="Invalid input").open()
            return
        try:
            try:
                save_attandance_in_db(set(rolls), key)
            except TypeError:
                save_attandance_in_db(set(rolls))
            Snackbar(text="Manual attendance saved").open()
        except Exception as e:
            Snackbar(text=f"Save failed: {e}").open()


MyApp().run() 