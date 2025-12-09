from deepface import DeepFace 
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
import time
from plotly_graph import all_student_graph,one_student_graph,convert_date_format,one_month_attandace_graph,attendance_graph_between_dates
from fact_db import fatch_roll_number,kivy_login
from kivy.uix.filechooser import error
from kivymd.uix.behaviors import HoverBehavior
from kivymd.uix.backdrop.backdrop import MDFloatLayout
# from kivy.config import Config
# Config.set('graphics', 'borderless', 0)
# Config.set('graphics', 'background_color', '1 1 1 1')
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.tools.hotreload.app import MDApp

# from kaki.app import App
from kivymd.uix.backdrop.backdrop import MDBoxLayout
from kivy.properties import ObjectProperty
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
from kivymd.uix.button import MDRaisedButton,MDRoundFlatButton,MDRectangleFlatIconButton
from kivymd.uix.selectioncontrol import MDSwitch
# warnings.filterwarnings("ignore")
# from kivy.config import Config
# Config.set('kivy', 'log_level', 'error')  # show only errors

from threading import Thread
import cv2 as cv
from kivy.properties import ObjectProperty
import time as t

# from kivy_reloader import Reloader
# from kivy_reloader.app import App


def show_snackbar(self, message, error=True):    
        # Beautiful Material Design Colors
        ERROR_COLOR = (1.0, 0.42, 0.42, 1)    # #FF5252 - Vibrant Red A200
        SUCCESS_COLOR = (0.30, 0.69, 0.31, 1) # #4CAF50 - Fresh Green 500
        
        try:
            # Create snackbar with small height (10dp)
            snackbar = Snackbar(
                duration=2.0,                           # Shorter duration for small snackbar
                size_hint_y=None,                       # Required for fixed heightṇ
                snackbar_x="10dp",                      # Side margins
                snackbar_y=dp(6),                       # Lower position for small snackbar
                height=dp(10),                          # SMALL HEIGHT (10dp)
                size_hint_x=0.85,                       # Width
                radius=[dp(5), dp(5), dp(5), dp(5)],    # Smaller radius for small height
                pos_hint={"center_x": 0.5},             # Centered
                elevation=6,                            # Slightly less shadow
            )
            
            # Set vibrant background color
            if error:
                snackbar.md_bg_color = ERROR_COLOR        # Vibrant Red
            else:
                snackbar.md_bg_color = SUCCESS_COLOR      # Fresh Green
            
            # Create SMALL label for 10dp height
            label = MDLabel(
                text=message,
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),               # White text
                size_hint_y=None,
                height=dp(8),                          # Even smaller label (8dp inside 10dp)
                padding=[dp(8), dp(1)],                # Minimal padding for small height
                halign="center",                       # Centered text
                valign="middle",                       # Vertically centered
                font_size="8sp",                       # VERY SMALL font for 10dp height
                bold=True,                             # Bold for emphasis
                font_name="Roboto",                    # Clean font
                line_height=0.9,                       # Tighter line spacing
                shorten=True,                          # Allow text shortening
                shorten_from="right",                  # Shorten from right
                max_lines=1,                           # Single line only
            )
            snackbar.add_widget(label)
            
            # Initial state - hidden below screen
            snackbar.opacity = 0
            snackbar.y = -dp(50)                       # Start position closer for small snackbar
            
            # Calculate final position
            final_y = dp(6)                            # Matches snackbar_y
            
            # SIMPLIFIED ANIMATION for small snackbar
            def animate_in():
                # Single combined animation for small snackbar
                Animation(
                    y=final_y,
                    opacity=1,
                    duration=0.25,
                    t='out_quad'
                ).start(snackbar)
            
            def animate_out():
                Animation(
                    y=-dp(50),
                    opacity=0,
                    duration=0.2,
                    t='in_quad'
                ).start(snackbar)
                Clock.schedule_once(lambda dt: snackbar.dismiss(), 0.2)
            
            # Schedule animations
            Clock.schedule_once(lambda dt: animate_in(), 0.1)
            Clock.schedule_once(lambda dt: animate_out(), snackbar.duration)
            
            # Open the snackbar
            snackbar.open()
            
            return snackbar
            
        except Exception as e:
            print(f"Snackbar error: {str(e)}")
            # Fallback with proper small height
            try:
                fallback_snackbar = Snackbar(
                    text=message,
                    duration=1.5,
                    snackbar_y=dp(6),
                    size_hint_x=0.85,
                    size_hint_y=None,
                    height=dp(10),
                    radius=[dp(5), dp(5), dp(5), dp(5)],
                    pos_hint={"center_x": 0.5},
                )
                # Try to set color
                try:
                    fallback_snackbar.md_bg_color = ERROR_COLOR if error else SUCCESS_COLOR
                except:
                    pass
                fallback_snackbar.open()
            except:
                Snackbar(text=message, duration=1.5).open()
                





class Screen_mange(MDScreenManager):
   
    def login_re(self, user, pas):
        login_status,massage = kivy_login(user.text, pas.text)
        if login_status:
            show_snackbar(self,message="Login successful", error=False)
            
            self.current = "main"
            
        else:
            show_snackbar(self,message=massage, error=True)
        
    def on_kv_post(self, base_widget):
        check_table()

class Home(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)



class Nav_graph_manager(MDScreenManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lay=ObjectProperty(None)

         
        # self.current="one_student"

    def on_kv_post(self, base_widget):
        self.current="one_student"
        Clock.schedule_once(self.print_main_screen, 0)
       

    def print_main_screen(self, dt):
        app = MDApp.get_running_app()
        print(app.root.get_screen("main").ids.main_screen_manager_home.get_screen("home").ids.nav_graph_manager.get_screen("one_student"))   
        # print(self.root.ids.nav_graph_manager)

       
    def get_screen_graph(self,values):
        print(f"i am from {values}")
        self.current=values

class One_student(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # def get_one(self):
        # try:
        #     roll=self.ids.one_student_roll.text
        #     date=self.ids.one_student_date.text
        #     img=one_student_graph(roll,convert_date_format(date))
        #     with open("test_one.png", "wb") as f:
        #       f.write(img)
        #       print("img is reload")
        #     self.ids.img_one.source="test_one.png"
        #     self.ids.img_one.reload()
        # except:
        #     print("Enter a vaild number and date -> ",img) 

    def get_one(self):
        roll_text = (self.ids.one_student_roll.text or "").strip()
        date_text = (self.ids.one_student_date.text or "").strip()

        try:
            roll = int(roll_text)
        except ValueError:
            print("Invalid roll number:", roll_text)
            show_snackbar(self,message="Invalid roll number", error=True)
            return

        date_conv = convert_date_format(date_text)
        if not date_conv:
            print("Invalid date format:", date_text)
            show_snackbar(self,message="Invalid date format", error=True)
            return

        if 'one_student_graph' not in globals():
            print("Graph function not loaded yet")
            show_snackbar(self,message="Graph function not loaded yet", error=True)
            return

        try:
            img_bytes = one_student_graph(roll, date_conv)
            if not img_bytes:
                print("one_student_graph returned no image for", roll, date_conv)
                show_snackbar(self,message="No data for given roll/date", error=True)
                return
            fname ="test_one.png"
            with open(fname, "wb") as f:
                f.write(img_bytes)
            # bust cache and reload on next fram
            self.ids.img_one.source = fname
            self.ids.img_one.reload()
            print("img reloaded:", fname)
            show_snackbar(self,message="Graph generated successfully", error=False)
        except Exception as e:
            show_snackbar(self,message="Error generating graph", error=True)
            print("Error generating one_student graph:", e)

class All_student(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def get_all(self):
        img=False
        try:
            date=self.ids.get_all_date.text
            img,error_massage=all_student_graph(convert_date_format(date))
            if not img:
                show_snackbar(self,message=error_massage, error=True)
                return
            if img != False :
                with open("test_all.png", "wb") as f:
                    f.write(img)
                    print("img is reload")
                self.ids.img_all.source="test_all.png"
                self.ids.img_all.reload()
                show_snackbar(self,message="Graph generated successfully", error=False)
        except error as e:
            show_snackbar(self,message="Invalid Roll Number Or Date", error=True)
            print(e,"Enter a vaild number and date -> ",img) 

    
class One_month(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_month(self):
        try:
            month_str = self.ids.get_all_month.text.strip()
            try:
                month = int(month_str)

                if month < 1 or month > 12:
                    print("Month must be between 1 and 12")
                    show_snackbar(self,message="Month must be between 1 and 12", error=True)
                    return
            except ValueError:
                print("Month must be a number")
                show_snackbar(self,message="Month must be a number", error=True)
                return

            # Generate and save the graph (it overwrites previous file)
            success,massage = one_month_attandace_graph(month)
            print(f"Graph generation success status: {success}")
            if success:
                # Update Kivy Image widget
                self.ids.img_all_month.source = "test_all_month.png"
                self.ids.img_all_month.reload()
                print("Attendance graph updated successfully")
                show_snackbar(self,message="Graph generated successfully", error=False)
            else:
                show_snackbar(self,message="Failed to generate attendance graph", error=True)
                print("Failed to generate attendance graph for this month:", month)

        except Exception as e:
            print(f"Error in get_month: {e}")
            show_snackbar(self,message="Error generating graph", error=True)


class Date_to_date(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def date_to_date(self):
        img=False
        try:
            starting_date=self.ids.starting_date.text
            ending_date=self.ids.ending_date.text          
            img,massage=attendance_graph_between_dates(starting_date,ending_date)
            if img==False:
                show_snackbar(self,message=massage, error=True)
                return
            if img :
                self.ids.date_to_date.source="date_to-date.png"
                self.ids.date_to_date.reload()
                show_snackbar(self,message="Graph generated successfully", error=False)
        except error as e:
            print(e,"Enter a vaild number and date -> ",img)
            show_snackbar(self,message="Invalid Date Format", error=True)



class Navigation(MDFloatLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def resize(self):
        pass
class List_button(HoverBehavior,MDRectangleFlatIconButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.theme_text_color = "Custom"
        self.text_color = (1, 1, 1, 1)
        self.md_bg_color = (.2, .45, .34, 1)
        self.icon_color = (1, 1, 1, 1)
        self.line_color=(1, 1, 1, 1  )
    def on_enter(self):
        self.md_bg_color=(.2,.22,.234,1)  
        self.text_color=(1,1,1,1)
    def on_leave(self):
        self.md_bg_color=(.2,.45,.34,1)  
        self.text_color=(1,1,1,1)
        
class Graph(MDFloatLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_one(self):
        try:
            roll=self.ids.one_student_roll.text
            date=self.ids.one_student_date.text
            img=one_student_graph(roll,convert_date_format(date))
            with open("test_one.png", "wb") as f:
              f.write(img)
            self.ids.img_one.source="test_one.png"
            self.ids.img_one.reload()
        except:
            print("Enter a vaild number and date")   

       
    def get_all(self):
        try:
            date=self.ids.get_all_date.text
            img=all_student_graph(convert_date_format(date))
            with open("test_all.png", "wb") as f:
                f.write(img)
            self.ids.img_all.source="test_all.png"
            self.ids.img_all.reload()
        except:
            print("Enter a valid number and date")    

    # with open("test_all.png", "wb") as f:
    #     f.write(img_bytes_all)
        
   

class Imag1(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cap = cv.VideoCapture(0)
        self.frame_rgb = None
        self.save_imag = None
        self.cap_live = None

        self.source = "imag\\save.png"
        # C:\Users\JEMIN\Desktop\kivymd\basic\imag\login_img.png

  


    def show_snackbar(self, message, error=True):    
        # Beautiful Material Design Colors
        ERROR_COLOR = (1.0, 0.42, 0.42, 1)    # #FF5252 - Vibrant Red A200
        SUCCESS_COLOR = (0.30, 0.69, 0.31, 1) # #4CAF50 - Fresh Green 500
        
        try:
            # Create snackbar with small height (10dp)
            snackbar = Snackbar(
                duration=2.0,                           # Shorter duration for small snackbar
                size_hint_y=None,                       # Required for fixed heightṇ
                snackbar_x="10dp",                      # Side margins
                snackbar_y=dp(6),                       # Lower position for small snackbar
                height=dp(10),                          # SMALL HEIGHT (10dp)
                size_hint_x=0.85,                       # Width
                radius=[dp(5), dp(5), dp(5), dp(5)],    # Smaller radius for small height
                pos_hint={"center_x": 0.5},             # Centered
                elevation=6,                            # Slightly less shadow
            )
            
            # Set vibrant background color
            if error:
                snackbar.md_bg_color = ERROR_COLOR        # Vibrant Red
            else:
                snackbar.md_bg_color = SUCCESS_COLOR      # Fresh Green
            
            # Create SMALL label for 10dp height
            label = MDLabel(
                text=message,
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),               # White text
                size_hint_y=None,
                height=dp(8),                          # Even smaller label (8dp inside 10dp)
                padding=[dp(8), dp(1)],                # Minimal padding for small height
                halign="center",                       # Centered text
                valign="middle",                       # Vertically centered
                font_size="8sp",                       # VERY SMALL font for 10dp height
                bold=True,                             # Bold for emphasis
                font_name="Roboto",                    # Clean font
                line_height=0.9,                       # Tighter line spacing
                shorten=True,                          # Allow text shortening
                shorten_from="right",                  # Shorten from right
                max_lines=1,                           # Single line only
            )
            snackbar.add_widget(label)
            
            # Initial state - hidden below screen
            snackbar.opacity = 0
            snackbar.y = -dp(50)                       # Start position closer for small snackbar
            
            # Calculate final position
            final_y = dp(6)                            # Matches snackbar_y
            
            # SIMPLIFIED ANIMATION for small snackbar
            def animate_in():
                # Single combined animation for small snackbar
                Animation(
                    y=final_y,
                    opacity=1,
                    duration=0.25,
                    t='out_quad'
                ).start(snackbar)
            
            def animate_out():
                Animation(
                    y=-dp(50),
                    opacity=0,
                    duration=0.2,
                    t='in_quad'
                ).start(snackbar)
                Clock.schedule_once(lambda dt: snackbar.dismiss(), 0.2)
            
            # Schedule animations
            Clock.schedule_once(lambda dt: animate_in(), 0.1)
            Clock.schedule_once(lambda dt: animate_out(), snackbar.duration)
            
            # Open the snackbar
            snackbar.open()
            
            return snackbar
            
        except Exception as e:
            print(f"Snackbar error: {str(e)}")
            # Fallback with proper small height
            try:
                fallback_snackbar = Snackbar(
                    text=message,
                    duration=1.5,
                    snackbar_y=dp(6),
                    size_hint_x=0.85,
                    size_hint_y=None,
                    height=dp(10),
                    radius=[dp(5), dp(5), dp(5), dp(5)],
                    pos_hint={"center_x": 0.5},
                )
                # Try to set color
                try:
                    fallback_snackbar.md_bg_color = ERROR_COLOR if error else SUCCESS_COLOR
                except:
                    pass
                fallback_snackbar.open()
            except:
                Snackbar(text=message, duration=1.5).open()
                
                


    def video_(self):
        self.cap.release()              # close previous
        self.cap = cv.VideoCapture(0) 
        self.cap_live = Clock.schedule_interval(self.video_display, 1 / 30.0)
       

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
        
        error_state = False
        print(f"name is {name.text} \n roll number is {roll.text} \n mobli is {mobile_number.text}")
        if not name.text:
            self.show_snackbar(message="Name cannot be empty", error=True)
            error_state = True 
            return
        if not roll.text:
            self.show_snackbar(message="Roll number cannot be empty", error=True)
            error_state = True 
            return

        if not mobile_number.text:
            self.show_snackbar(message="Mobile number cannot be empty", error=True)
            error_state = True 
            return

        if not self.save_imag is not None:
            self.show_snackbar(message="Please capture an image", error=True)
            error_state = True 
            return
        
        if not error_state:
            mobile_number=mobile_number.text
            name=name.text
            roll=roll.text
            if name:
                    if name.isdigit():
                        self.show_snackbar(message="Name is not contain digit",error=True)

            
            if roll:
                all_roll=fatch_roll_number()
                if not roll.isdigit():
                    self.show_snackbar(message="Roll number must contain only digits", error=True)
                    return False
                
                if int(roll) in all_roll:
                    self.show_snackbar(message="Roll number already exists", error=True)
                    return False
                

            if mobile_number:
                if not mobile_number.isdigit():
                    self.show_snackbar(message="Mobile number must contain only digits", error=True)
                    return False
                
                
                if len(mobile_number) != 10:
                    self.show_snackbar(message="Mobile number must be 10 digits long", error=True)
                    return False
            
      
        """release camara """
        try:
            # Save the captured image
            save_path = r"D:\SmartAttendanceSystem\Kivy_app\attendance\{}.jpg".format(roll)
            cv.imwrite(save_path, self.save_imag)

            # Restart camera
            self.re_camara() 

            # Load default image
            defult_img = cv.imread(r"D:\SmartAttendanceSystem\Kivy_app\imag\save.png")
            print("default img load")
            defult_img = cv.flip(defult_img, 0)
            defult_img = cv.cvtColor(defult_img, cv.COLOR_BGR2RGB)

            # Convert to Kivy texture
            texture = Texture.create(size=(defult_img.shape[1], defult_img.shape[0]), colorfmt='rgb')
            texture.blit_buffer(defult_img.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            self.texture = texture

        except Exception as e:
            print(f"Error: {e}")  # Optional: print exact error for debugging
            self.show_snackbar(message="Error in saving image in database 1")
            return

        """save student info in database"""
        try:
            success, buffer = cv.imencode(".jpg", self.save_imag)
            binary_data = buffer.tobytes()
            insert_into_student_info(int(roll),name,mobile_number,binary_data)
            self.show_snackbar(message="img is save ",error=False)
        except:
            print("error in save student info in database")
            self.show_snackbar(message="Error in save image in database 2")
            
    def re_camara(self):
        print("start attandace camara not available")
        self.cap_live.cancel()
        self.cap.release()
        self.source = "imag\\save.png"
def mode_load():
        # global DeepFace
        pass
        # from deepface import DeepFace 
        
class Start_attandance(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cap = cv.VideoCapture(0)
        self.cap_live = None
        self.save_imag = None
        self.frame_rgb = None
        self.present = set()
        Thread(target=mode_load).start()
    

    def video_(self):
        try:
            self.cap = cv.VideoCapture(0)
        except:
            pass
        try:
            self.cap_live = Clock.schedule_interval(self.video_display, 1 / 30.0)
            print(self.present)  
        except:
            pass
    def video_display(self, dt):
        
        try:
            ret, frame = self.cap.read()
            if ret:
                faces = DeepFace.extract_faces(
                    img_path=frame,
                    detector_backend="opencv",
                    enforce_detection=False,
                    align=True
                )
                for face in faces:
                    box = face["facial_area"]
                    x, y, w, h = box["x"], box["y"], box["w"], box["h"]
                    cv.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                dis_img = cv.flip(frame, 0)
                self.frame_rgb = cv.cvtColor(dis_img, cv.COLOR_BGR2RGB)
                texture = Texture.create(size=(dis_img.shape[1], dis_img.shape[0]), colorfmt='rgb')
                texture.blit_buffer(self.frame_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                self.texture = texture
                try:
                    re = DeepFace.find(
                        img_path=frame,
                        db_path=r"D:\SmartAttendanceSystem\Kivy_app\attendance",
                        detector_backend="opencv",
                        model_name="SFace",
                        enforce_detection=False
                    )
                except:
                    print("model is not load")    
                for i, df in enumerate(re):
                    print(f"\nFace {i+1} match:")
                    if len(df) > 0:
                        top = df.iloc[0]
                        name = top["identity"].split("\\")[-1].split(".")[0]
                        distance = top["distance"]
                        if name not in self.present:
                            show_snackbar(self,message=f"Present: {name} Attandace save in DB", error=False)
                        self.present.add(name)
                        print(f"✅ Matched: {name} (Distance: {distance:.3f})")
                    else:
                        print("❌ No match found")
                if cv.waitKey(1) & 0xFF == ord("q"):
                    self.cap_live.cancel()
                    
        except:
            print("model not load")            

    def re_camara(self):
        print("start attandace camara not available")
        if self.present:
            pass_ar=self.present
            print(pass_ar)
            save_attandance_in_db(pass_ar)
        else :
            print("not start")    
        # print(self.present)
        try:
            self.cap_live.cancel()
            self.cap.release() 
            print("Camera resources released successfully")
        except:
            print("Error releasing camera resources")

class Setting(MDScreen):
    dynamic_input_box = ObjectProperty(None)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        
        self.s_h_x=.1
        self.s_h_y=.1
        self.lature_time=[]
        self.dynamic_input_pto=[]

    def time_manage(self, t):
        print("Adding dynamic fields...")
        self.dynamic_input_box.clear_widgets()
        
        try:
            num = int(t)
        except ValueError:
            num = 1  # fallback if input is invalid
        new_fild=[]
        start_field, end_field = None, None
        for i in range(num):

            inner_layout=MDBoxLayout(orientation="horizontal",size_hint_y=None,size_hint_x=.5)

            str= MDTextField(
                hint_text=f"Lecture {i + 1}",
                mode="rectangle",
                size_hint_x=.15               
              
            )
            new_fild.append(str)
            text_to=MDLabel(text=" to ",size_hint=(None,None),halign="center",valign="middle")

            end = MDTextField(
                hint_text=f"Lecture {i + 1}",
                mode="rectangle",
                # size_hint_x=.1
                size_hint_x=.15
            )
            new_fild.append(end)
            
            self.dynamic_input_pto.append(new_fild)
            self.lature_time.append((str, end))
            inner_layout.add_widget(str)
            inner_layout.add_widget(text_to)
            inner_layout.add_widget(end)


            self.dynamic_input_box.add_widget(inner_layout)
            # print(f"fild add {self.dynamic_input_box.children[-1].hint_text}")
        button_lat=MDRaisedButton(text="Add Lecture",
                            pos_hint={"x": 0.5},
                            on_press=self.print_dynamic_input
                            )
        self.dynamic_input_box.add_widget(button_lat) 

    def print_dynamic_input(self,dt):
        print(len(self.dynamic_input_pto))
        for i, (start_field, end_field) in enumerate(self.dynamic_input_pto):
            print(f"Lecture {i + 1}: {start_field.text} --> {end_field.text}")
            print("-----")


    

class MyApp(MDApp):


    
    def db_load(self):
        global create_table_attandace, create_table_store_date,create_table_student_info,insert_into_student_info, update_into_setting_theam, update_into_setting_auto, create_row_for_lacture,get_theme_form_setting,save_attandance_in_db,check_table
        from connect_db import   create_table_attandace, create_table_store_date,create_table_student_info
        from crud_in_database import insert_into_student_info, update_into_setting_theam, update_into_setting_auto, create_row_for_lacture,get_theme_form_setting,save_attandance_in_db,check_table
        from fact_db import fatch_all_studebent_attandance,fatch_one        


    def build(self):  
        # return Builder.load_file("my.kv")
        return Screen_mange()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auto = None  
        self.time_auto_man = []
        self.lacture_lay = BoxLayout()
        self.text_input = []
        self.db_load()
        Thread(target=self.load_g).start()  
    def load_g(self):
        global all_student_graph,one_student_graph,convert_date_format
        from plotly_graph import all_student_graph,one_student_graph,convert_date_format,one_month_attandace_graph
    def theme_change(self, active):
        print(f"Switch State: {active}")
        if active:
            self.theme_cls.theme_style = "Dark"
            update_into_setting_theam('Dark')
            # switch.active=True          
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
        
                self.attendance.cap.release()
    def get_screen_graph(self,value):
        app = MDApp.get_running_app()
        # nav_manager = (
        #     app.root.ids.main_screen_manager
        #     .get_screen("main").ids.main_screen_manager_home.ids.home_screen
        #     .get_screen("home").ids.nav_graph_manager
        # )
        # print("it will get -> ",nav_manager)
    



if __name__ == "__main__":
    MyApp().run()
