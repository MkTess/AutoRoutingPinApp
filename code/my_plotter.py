import wx

class MatrixDisplay(wx.Control):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent,style = wx.NO_BORDER)

        self.parent = parent
        self.font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                            wx.FONTWEIGHT_NORMAL, False, 'Courier 10 Pitch')
        
        self.cell_size = 0

        self.matrix = [[0 for _ in range(5)] for _ in range(5)]
        self.pin_to_draw = 0
        self.prev_cell = []

        self.is_highlighted = False

        self._Buffer = None

        self.is_drawing = False
        self.event_mappings = {
            wx.EVT_ENTER_WINDOW: self.OnInside,
            wx.EVT_LEAVE_WINDOW: self.OnOutside,
            wx.EVT_LEFT_DOWN: self.OnClick,
            wx.EVT_MOTION: self.OnMouseMove
        }

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.resize()

    def external_draw(self,*param,**kargs):
        if len(param) == 3:
            val,i,j = param
            i,j = i-1,j-1
            self.matrix[i][j] = val
            self.draw_cell(wx.ClientDC(self),val,i,j)
        
        if "matrix" in kargs: self.matrix = kargs["matrix"]; self.resize(); self.UpdateDrawing()

    def DoGetBestClientSize(self):
        return self.GetSize()

    def OnMouseMove(self, e):
        if self.is_highlighted:
            y, x = self.relative_cursor_position()
            if [x, y] != self.prev_cell:
                if self.pin_to_draw == 0:
                    if self.prev_cell :
                        self.draw_cell(wx.ClientDC(self), self.matrix[self.prev_cell[0]][self.prev_cell[1]], *self.prev_cell)

                    if self.matrix[x][y] != 0:
                        self.draw_cell(wx.ClientDC(self),0 , x, y)
                    self.prev_cell = [x, y]

                else:
                    if self.prev_cell :
                        self.draw_cell(wx.ClientDC(self), 0, *self.prev_cell)

                    if self.matrix[x][y] == 0:
                        self.draw_cell(wx.ClientDC(self), self.pin_to_draw, x, y)
                        self.prev_cell = [x, y]

    def OnClick(self, _):
        if self.prev_cell:
            self.matrix[self.prev_cell[0]
                        ][self.prev_cell[1]] = self.pin_to_draw
            self.prev_cell = []

    def OnInside(self, e):
        self.is_highlighted = True

    def OnOutside(self, e):
        self.is_highlighted = False
        if self.prev_cell:
            if self.pin_to_draw == 0: 
                self.draw_cell(wx.ClientDC(self), self.matrix[self.prev_cell[0]][self.prev_cell[1]], *self.prev_cell)
            else:
                self.draw_cell(wx.ClientDC(self), 0, *self.prev_cell)
        self.prev_cell = []

    def OnSize(self, e):
        e.Skip()
        self.resize()

    def OnPaint(self, e): dc = wx.BufferedPaintDC(self, self._Buffer)

    def UpdateDrawing(self):
        dc = wx.MemoryDC()
        dc.SelectObject(self._Buffer)
        dc.SetBackground(wx.WHITE_BRUSH)
        for i, row in enumerate(self.matrix):
            for j, val in enumerate(row):
                self.draw_cell(dc, val, i, j)

        del dc
        self.Refresh(eraseBackground=False)
        self.Update()



    def set_pin_drawing_mode(self, pin):
        self.pin_to_draw = pin
        if not self.is_drawing:
            for evt, evt_hndlr in self.event_mappings.items(): self.Bind(evt,evt_hndlr)
            self.is_drawing = True

    def set_normal_mode(self):
        if self.is_drawing:
            for evt in self.event_mappings: self.Bind(evt,None)
            self.pin_to_draw = None
            self.is_drawing = False

    def compute_size(self, box_size):
        cell_count_width = len(self.matrix)
        cell_count_height = len(self.matrix[0])

        self.cell_size = int(box_size/cell_count_width)
        self.font.SetPixelSize((0, int(self.cell_size*0.8)-1))
        self.SetSize((cell_count_height*self.cell_size, cell_count_width*self.cell_size))

        self._Buffer = wx.Bitmap(*self.ClientSize)
        self.UpdateDrawing()
        self.InvalidateBestSize()
        
    def relative_cursor_position(self):
        return [int((a-b)/self.cell_size) for a, b in zip(wx.GetMousePosition(), self.GetScreenPosition())]
    
    def center_text(self, dc, text, x, y):
        dimensions = [i/2 for i in dc.GetTextExtent(text)]
        return int((y+1/2)*self.cell_size - dimensions[0]), int((x+1/2)*self.cell_size - dimensions[1])

    def resize(self):
        dims = self.parent.GetSize()
        dims[0] -= 30
        dims[1] -= 50+30+20+20+45
        self.compute_size(min(dims))



    def draw_cell(self, dc: wx.DC, val, i, j):
        dc.SetFont(self.font)
        dc.SetPen(wx.TRANSPARENT_PEN)

        rec_col = wx.GREEN_BRUSH
        tex_col = wx.BLACK

        if isinstance(val, list):
            rec_col = wx.Brush(self.GetBackgroundColour())
            dc.SetBrush(rec_col)
            dc.DrawRectangle(j*self.cell_size, i*self.cell_size,
                         self.cell_size, self.cell_size)
            dc.SetPen(wx.BLACK_PEN)
            dc.SetBrush(wx.BLACK_BRUSH)
            dc.DrawCircle(self.center_text(dc, str(""), i, j), self.cell_size/8)
            dc.DrawLine(self.center_text(dc, str(""), i, j), [int( x + y*self.cell_size/2) for x, y in zip(self.center_text(dc, str(""), i, j), [val[1], val[0]])])
            dc.SetPen(wx.TRANSPARENT_PEN)
            return

        if val == "Z" or val == "B":
            rec_col = wx.BLACK_BRUSH
            tex_col = wx.RED
        elif val == "E":
            rec_col = wx.RED_BRUSH
        elif val == "F":
            rec_col = wx.YELLOW_BRUSH
        elif val == "B":
            return
        elif val == 0:
            rec_col = wx.Brush(self.GetBackgroundColour())

        dc.SetBrush(rec_col)
        dc.DrawRectangle(j*self.cell_size, i*self.cell_size,
                         self.cell_size, self.cell_size)
        dc.SetTextForeground(tex_col)
        if val != 0:
            dc.DrawText(str(val), self.center_text(dc, str(val), i, j))
