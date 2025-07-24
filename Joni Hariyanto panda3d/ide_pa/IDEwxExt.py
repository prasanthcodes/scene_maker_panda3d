__all__=['SortableListCtrl','myIntSpinCtrl']

import wx
from wx.lib.intctrl import IntCtrl
from wx.lib.mixins.listctrl import ColumnSorterMixin


class SortableListCtrl(wx.ListCtrl, ColumnSorterMixin):
    def __init__(self, *args,**kw):
        images=kw.pop('images') if 'images' in kw else 0
        wx.ListCtrl.__init__(self, *args,**kw)
        if images:
           # if the image list is garbage collected, no image will be drawn
           self.imagesList=images
           # only IMAGE_LIST_SMALL works
           self.SetImageList(images,wx.IMAGE_LIST_SMALL)
        self.strConv=self.sortDataBuilder=None

    def setStrConverter(self,strConv):
        self.strConv=strConv

    def setSortDataBuilder(self,sortDataBuilder):
        self.sortDataBuilder=sortDataBuilder

    def initSorter(self,rows=[],init=True):
        self.itemDataMap={}
        if self.strConv is None:
           self.strConv=self.sortDataBuilder=[str]*self.GetColumnCount()
        r=0
        for rd in rows:
            self.Append([self.strConv[rd.index(c)](c) for c in rd])
            self.SetItemData(r,r)
            self.itemDataMap[r]=[self.sortDataBuilder[rd.index(c)](c) for c in rd]
            r+=1
        if init:
           ColumnSorterMixin.__init__(self,self.GetColumnCount())
        self.lastSortedCol=-1

    def GetListCtrl(self):
        return self

    def GetSortImages(self):
        return 0,1

    def OnSortOrderChanged(self):
#         print 'colClicked:',self._col
        # gee, ColumnSorterMixin doesn't clear
        # the last sorted column's sort order flag.....
        resorted=self._col!=self.lastSortedCol
        if resorted:
#            print self.lastSortedCol
           # so, clear it
           self._colSortFlag[self.lastSortedCol]=0
           # and sort it again
           self.SortListItems(self._col)
           self.lastSortedCol=self._col
        return resorted


class myIntSpinCtrl(IntCtrl):
  def __init__(self, *args,**kw):
      self.onValueChangeCommand=kw.pop('onValueChange') if 'onValueChange' in kw else lambda:0
      self.extraArgs=kw.pop('extraArgs') if 'extraArgs' in kw else None
      IntCtrl.__init__(self, *args,**kw)
      self.Bind(wx.EVT_MOVE,self.OnMove)
      self.Bind(wx.EVT_SIZE,self.OnMove) # somehow, EVT_MOVE on Linux doesn't trigger anything
      self.Bind(wx.lib.intctrl.EVT_INT, self.OnValueChange)
      self.SC=wx.SpinButton(self.GetParent(),-1,size=(15,self.GetSize().height),style=wx.SP_VERTICAL)
      self.SC.Bind(wx.EVT_SPIN,self.OnSpin)
      self.SC.SetRange(self.GetMin(), self.GetMax())
      self.SC.SetValue(self.GetValue())

  def OnSpin(self,e):
      self.Value=str(self.SC.Value)

  def OnMove(self,e):
      pos=self.GetPosition()
      self.SC.SetPosition((pos.x+self.Size.width,pos.y))
      e.EventObject.GetParent().Refresh()

  def OnValueChange(self,e):
      val=self.GetValue()
      if self.SC.Value!=val:
         self.SC.Value=val
      if self.extraArgs is None:
         self.onValueChangeCommand(val)
      else:
         self.onValueChangeCommand(self.extraArgs,val)

