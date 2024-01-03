import os
import wx
from PIL import Image

class RoundButton(wx.Control):
    def __init__(self, parent, path, label = None, color = None):
        super(RoundButton, self).__init__(parent, -1, style=wx.BORDER_NONE)

        self.default_gray = 100
        self.icon = self.get_image_ref(path)
        self.normal_img = self.generate_normal_button()
        self.hover_img = self.generate_highlight_button(color) if color else None
        self.click_img = self.generate_click_button(color) if color else None

        self.SetSize(self.normal_img.GetSize())
        self.region = wx.Region(self.normal_img,wx.BLACK)

        self.hovered = False
        self.clicked = False

        if label: self.SetToolTip(label)

        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)

        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_window)

    def DoGetBestSize(self):
        return self.normal_img.GetSize()

    def post_event(self):
        event = wx.CommandEvent()
        event.SetEventObject(self)
        event.SetEventType(wx.EVT_BUTTON.typeId)
        wx.PostEvent(self, event)

    def on_size(self, event):
        event.Skip()
        self.Refresh()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour()))
        dc.Clear()
        bitmap = self.normal_img
        if self.clicked: bitmap = self.click_img or bitmap
        elif self.hovered: bitmap = self.hover_img or bitmap
        dc.DrawBitmap(bitmap, 0, 0)

    def on_left_down(self, event):
        x, y = event.GetPosition()
        if self.region.Contains(x, y):
            self.clicked = True
            self.Refresh()

    def on_left_up(self, event):
        if self.clicked:
            x, y = event.GetPosition()
            if self.region.Contains(x, y):
                self.post_event()
        self.clicked = False
        self.Refresh()

    def on_motion(self, event):
        x, y = event.GetPosition()
        if not self.hovered and self.region.Contains(x, y): self.hovered = True; self.Refresh()
        elif self.hovered and not self.region.Contains(x, y):  self.hovered = False;self.clicked = False; self.Refresh()

    def on_leave_window(self, event): self.hovered = False;self.clicked = False; self.Refresh()

    def set_color(self,color): 
        self.color = color
        self.hover_img = self.generate_highlight_button(color)
        self.click_img = self.generate_click_button(color)

    def get_image_ref(self,path):
        for root, dirs, files in os.walk("Resources"):
            for el in files:
                if path == el:
                    return Image.open(root + "/" + el)

    def generate_normal_button(self):
        big_mask = Image.open("Resources/big_mask.png")
        width, height = big_mask.size

        rez_img = Image.new("RGBA",(width,height))
        pixel_map = rez_img.load()

        for i in range(width):
            for j in range(height):
                a = big_mask.getpixel((i,j))[0]
                pixel_map[i,j] = (*[self.default_gray]*3,a)

        rez_img.paste(self.icon,mask = self.icon)
        return wx.Bitmap.FromBufferRGBA(*rez_img.size, rez_img.tobytes())

    def generate_highlight_button(self,color):
        big_mask = Image.open("Resources/big_mask.png")
        small_mask = Image.open("Resources/small_mask.png")
        width, height = big_mask.size

        rez_img = Image.new("RGBA",(width,height))
        pixel_map = rez_img.load()

        for i in range(width):
            for j in range(height):
                a = big_mask.getpixel((i,j))[0]
                pixel_map[i,j] = (*color,a)
        
        f = lambda a,b,x: int(a + ((b-a)/255)*x) 
        for i in range(width):
            for j in range(height):
                a = small_mask.getpixel((i,j))[0]
                if a != 0: 
                    pixel_map[i,j] = (*(f(pixel_map[i,j][cnt],self.default_gray,a) for cnt in range(3)),pixel_map[i,j][3])

        rez_img.paste(self.icon,mask = self.icon)
        return wx.Bitmap.FromBufferRGBA(*rez_img.size, rez_img.tobytes())

    def generate_click_button(self,color):

        big_mask = Image.open("Resources/big_mask.png")
        width, height = big_mask.size

        rez_img = Image.new("RGBA",(width,height))
        pixel_map = rez_img.load()

        for i in range(width):
            for j in range(height):
                a = big_mask.getpixel((i,j))[0]
                pixel_map[i,j] = (*color,a)
        
        rez_img.paste(self.icon,mask = self.icon)
        return wx.Bitmap.FromBufferRGBA(*rez_img.size, rez_img.tobytes())

class ColoredTab(wx.Panel):
    
    def __init__(self, parent, label = None, color = None):
        super(ColoredTab, self).__init__(parent, -1, style=wx.BORDER_NONE)

        self.color = color or (150,150,150)
        self.bg_color = parent.GetBackgroundColour()
        self.label = label or "none"
        self.size = (100,30)
        self.spacing = 10

        self.objects = []

        self.SetBackgroundColour(self.bg_color)

        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def DoGetBestSize(self):
        return self.size

    def add_object(self,obj):
        self.objects.append(obj)
        if isinstance(obj,RoundButton): obj.set_color(self.color)
        self.compute_size()
        self.arange_objects()
    
    def arange_objects(self):
        current_poz = self.spacing
        for obj in self.objects:
            obj.SetPosition((current_poz,30+self.spacing))
            current_poz += obj.GetBestSize()[0] + self.spacing

    def compute_size(self):
        width = (len(self.objects)+1)*self.spacing + sum(obj.GetBestSize()[0] for obj in self.objects)
        if width <= 130: width = 130
        height = max(obj.GetBestSize()[1] for obj in self.objects) + self.spacing*2 + 30 
        self.size = (width,height)

    def on_size(self, event):
        event.Skip()
        self.Refresh()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush(self.bg_color))

        dc.SetBrush(wx.Brush(self.color))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(0,0,self.GetSize()[0],30)

        dc.DrawText(self.label,self.center_text(dc,self.label))

    def center_text(self, dc, text):
        dimensions = [i/2 for i in dc.GetTextExtent(text)]
        return int(self.GetSize()[0]/2 - dimensions[0]), int(15 - dimensions[1])

class NewBoardDialog(wx.Dialog):
 
    def __init__(self, parent):
        super(NewBoardDialog, self).__init__(parent, -1)

        self.SetSize((305, 250))
        self.SetBackgroundColour(parent.GetBackgroundColour())
        self.font = wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, 'Courier 10 Pitch')
        self.SetTitle("Create new board")
        self.InitUI()


    def InitUI(self):

        pnl = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        sb = wx.StaticBox(pnl, label='New board size:')
        sb.SetForegroundColour(wx.WHITE)
        sb.SetFont(self.font)
        sbs = wx.StaticBoxSizer(sb, orient=wx.VERTICAL)


        normal_hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.squarerb = wx.RadioButton(pnl, label='square shape:    ', style = wx.RB_GROUP)
        self.squarerb.SetForegroundColour(wx.WHITE)
        self.squarerb.SetFont(self.font)
        normal_hbox.Add(self.squarerb)

        txt = wx.StaticText(pnl, label='Size:    ')
        txt.SetForegroundColour(wx.WHITE)
        txt.SetFont(self.font)
        normal_hbox.Add(txt)

        self.squarespnr = wx.SpinCtrl(pnl, initial = 10, min = 5, max = 50 , size = (50,30), style = wx.NO_BORDER)
        self.squarespnr.SetBackgroundColour((50,50,50))
        self.squarespnr.SetForegroundColour(wx.WHITE)
        self.squarespnr.SetFont(self.font)
        normal_hbox.Add(self.squarespnr)
        sbs.Add(normal_hbox)
        sbs.Add((0,20))



        custom_box = wx.BoxSizer(wx.HORIZONTAL)
        self.customrb = wx.RadioButton(pnl, label='custom shape:    ')
        self.customrb.SetForegroundColour(wx.WHITE)
        self.customrb.SetFont(self.font)
        custom_box.Add(self.customrb)

        sizes_box = wx.BoxSizer(wx.VERTICAL)

        width_box = wx.BoxSizer(wx.HORIZONTAL)
        txt = wx.StaticText(pnl, label='Width:   ')
        txt.SetForegroundColour(wx.WHITE)
        txt.SetFont(self.font)
        width_box.Add(txt)

        self.widthspnr = wx.SpinCtrl(pnl, initial = 10, min = 5, max = 50 , size = (50,30), style = wx.NO_BORDER)
        self.widthspnr.SetBackgroundColour((50,50,50))
        self.widthspnr.SetForegroundColour(wx.WHITE)
        self.widthspnr.SetFont(self.font)
        width_box.Add(self.widthspnr)
        sizes_box.Add(width_box)
        sizes_box.Add((0,10))


        height_box = wx.BoxSizer(wx.HORIZONTAL)
        txt = wx.StaticText(pnl, label='Height:  ')
        txt.SetForegroundColour(wx.WHITE)
        txt.SetFont(self.font)
        height_box.Add(txt)

        self.heightspnr = wx.SpinCtrl(pnl, initial = 10, min = 5, max = 50 , size = (50,30), style = wx.NO_BORDER)
        self.heightspnr.SetBackgroundColour((50,50,50))
        self.heightspnr.SetForegroundColour(wx.WHITE)
        self.heightspnr.SetFont(self.font)
        height_box.Add(self.heightspnr)
        sizes_box.Add(height_box)

        custom_box.Add(sizes_box)
        sbs.Add(custom_box)

        pnl.SetSizer(sbs)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)

        okButton = wx.Button(self,wx.ID_OK, label='Ok')
        okButton.SetFont(self.font)
        hbox2.Add(okButton)
        
        closeButton = wx.Button(self,wx.ID_CANCEL, label='Close')
        closeButton.SetFont(self.font)
        hbox2.Add(closeButton, flag=wx.LEFT, border=5)

        vbox.Add(pnl, proportion=1,
            flag=wx.ALL|wx.EXPAND, border=5)
        vbox.Add(hbox2, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

        self.SetSizer(vbox)

    def get_value(self):
        if self.squarerb.GetValue(): return (self.squarespnr.GetValue(),self.squarespnr.GetValue())
        else: return (self.widthspnr.GetValue(),self.heightspnr.GetValue())

class DrawDialog(wx.Dialog):

    def __init__(self, parent):
        super(DrawDialog, self).__init__(parent, -1)

        self.SetSize((250, 200))
        self.SetBackgroundColour(parent.GetBackgroundColour())
        self.font = wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, 'Courier 10 Pitch')
        self.SetTitle("Select pin to draw")
        self.InitUI()


    def InitUI(self):

        pnl = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        sb = wx.StaticBox(pnl, label='New board size:')
        sb.SetForegroundColour(wx.WHITE)
        sb.SetFont(self.font)
        sbs = wx.StaticBoxSizer(sb, orient=wx.VERTICAL)
        
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        
        self.spnrrb = wx.RadioButton(pnl, label='normal pin:    ', style = wx.RB_GROUP)
        self.spnrrb.SetForegroundColour(wx.WHITE)
        self.spnrrb.SetFont(self.font)
        hbox1.Add(self.spnrrb)

        self.spnr = wx.SpinCtrl(pnl, initial = 1, min = 1, max = 30 , size = (50,30), style = wx.NO_BORDER)
        self.spnr.SetBackgroundColour((50,50,50))
        self.spnr.SetForegroundColour(wx.WHITE)
        self.spnr.SetFont(self.font)

        hbox1.Add(self.spnr)
        sbs.Add(hbox1)
        
        urb = wx.RadioButton(pnl, label='Z pin')
        urb.SetForegroundColour(wx.WHITE)
        urb.SetFont(self.font)
        sbs.Add(urb)

        pnl.SetSizer(sbs)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)

        okButton = wx.Button(self,wx.ID_OK, label='Ok')
        okButton.SetFont(self.font)
        hbox2.Add(okButton)
        
        closeButton = wx.Button(self,wx.ID_CANCEL, label='Close')
        closeButton.SetFont(self.font)
        hbox2.Add(closeButton, flag=wx.LEFT, border=5)

        vbox.Add(pnl, proportion=1,
            flag=wx.ALL|wx.EXPAND, border=5)
        vbox.Add(hbox2, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

        self.SetSizer(vbox)

    def get_value(self):
        if self.spnrrb.GetValue(): return self.spnr.GetValue()
        else: return "Z"
