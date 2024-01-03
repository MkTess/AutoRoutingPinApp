import copy
import os
import threading
import wx
from ui_elements import ColoredTab,NewBoardDialog, DrawDialog
from ui_elements import RoundButton
from my_plotter import MatrixDisplay
from my_solver import Solver

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title)

        self.Center()
        self.InitUI()

        self.solver = Solver()
        self.solver.set_hook(self.pin_display.external_draw)

        self.Center()

    def InitUI(self):
        
        self.SetBackgroundColour(wx.Colour(40, 40, 40))
        self.SetSize(900,900)
        self.SetMinSize((600,700))

        drawing_tab = ColoredTab(self,"Drawing commands",(255,0,255))

        draw_btn = RoundButton(drawing_tab,"pencil.png", "draw pins")
        draw_btn.Bind(wx.EVT_BUTTON,self.OnDraw)
        drawing_tab.add_object(draw_btn)

        erase_btn = RoundButton(drawing_tab, "eraser.png", "erase pins")
        erase_btn.Bind(wx.EVT_BUTTON,self.OnErase)
        drawing_tab.add_object(erase_btn)

        mouse_btn = RoundButton(drawing_tab, "pointer.png", "stop drawing")
        mouse_btn.Bind(wx.EVT_BUTTON,self.OnNormal)
        drawing_tab.add_object(mouse_btn)


        files_tab = ColoredTab(self,"File Manipulation",(255,255,0))

        save_btn = RoundButton(files_tab, "save.png", "save as csv")
        save_btn.Bind(wx.EVT_BUTTON,self.OnSave)
        files_tab.add_object(save_btn)

        load_btn = RoundButton(files_tab, "load.png", "load from csv")
        load_btn.Bind(wx.EVT_BUTTON,self.OnLoad)
        files_tab.add_object(load_btn)
        

        board_tab = ColoredTab(self,"Board commands",(0,255,255))

        solve_btn = RoundButton(board_tab, "cogs.png", "generate conections")
        solve_btn.Bind(wx.EVT_BUTTON,self.OnGenerate)
        board_tab.add_object(solve_btn)

        validate_btn = RoundButton(board_tab, "check.png", "validate conections")
        validate_btn.Bind(wx.EVT_BUTTON,self.OnValidate)
        board_tab.add_object(validate_btn)

        new_board_btn = RoundButton(board_tab, "new.png", "create new board")
        new_board_btn.Bind(wx.EVT_BUTTON,self.OnNew)
        board_tab.add_object(new_board_btn)
        
        tabs_sizer = wx.BoxSizer(wx.HORIZONTAL)


        tabs_sizer.Add(drawing_tab)
        tabs_sizer.AddSpacer(20)
        tabs_sizer.Add(files_tab)
        tabs_sizer.AddSpacer(20)
        tabs_sizer.Add(board_tab)

        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(tabs_sizer,flag=wx.ALIGN_CENTER)
        vbox.Add((-1, 10))

        self.pin_display = MatrixDisplay(self)

        vbox.Add(self.pin_display,flag = wx.CENTER)
        self.SetSizer(vbox)

    def OnDraw(self,_):
        with DrawDialog(self) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.pin_display.set_pin_drawing_mode(dlg.get_value())
                
    def OnErase(self,_):
        self.pin_display.set_pin_drawing_mode(0)

    def OnNormal(self,_):
        self.pin_display.set_normal_mode()

    def OnLoad(self,_):

        with wx.FileDialog(self, "Choose a file to load", "", "", "*.csv", wx.FD_OPEN) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.filename = dlg.GetFilename()
                self.dirname = dlg.GetDirectory()
                self.solver.read_from_csv(os.path.join(self.dirname, self.filename))

    def OnSave(self,_):
        
        with wx.FileDialog(self, "Save your board as csv", "", "", "*.csv", wx.FD_OPEN) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.filename = dlg.GetFilename()
                self.dirname = dlg.GetDirectory()
                self.solver.set_matrix(copy.deepcopy(self.pin_display.matrix))
                self.solver.write_to_csv(os.path.join(self.dirname, self.filename))

    def OnGenerate(self,_):
        self.solver.set_matrix(copy.deepcopy(self.pin_display.matrix))
        x = threading.Thread(target=self.solver.solve)
        x.start()

    def OnValidate(self,_):
        x = threading.Thread(target=self.solver.validate_solution)
        x.start()

    def OnNew(self,_):
        with NewBoardDialog(self) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.solver.generate_empty_matrix(dlg.get_value())

app = wx.App(False)
frame = MainWindow(None, "Sample editor")
frame.Show()
app.MainLoop()
