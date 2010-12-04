#!/usr/bin/python
# -*- coding:utf-8 -*-
#
# Author: mfumi <m.fumi760@gmail.com>
# Version: 0.0.1
# License: NEW BSD LICENSE
#  Copyright (c) 2010, mfumi
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the mfumi nor the names of its contributors may be used to endorse or promote products derived from this software without
#      specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
#  TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import datetime
import re
import time
import webbrowser

import Skype4Py
import urwid


##############################################################################


class MyListBox(urwid.ListBox):
    def __init__(self,body):
        super(MyListBox,self).__init__(body)

    def keypress(self,size,key):
        if key == 'j':
            self.keypress(size,'down')
        if key == 'ctrl d':
            self.keypress(size,'page down')
        elif key == 'k':
            self.keypress(size,'up')
        elif key == 'ctrl u':
            self.keypress(size,'page up')
        elif key == 'g':
            self.set_focus_top()
        elif key == 'G':
            self.set_focus_bottom()
        else:
            return super(MyListBox,self).keypress(size,key)

    def set_focus_bottom(self):
        try:
            if isinstance(self.body[-1],urwid.Divider):
                self.body.set_focus(len(self.body)-2)
            else:
                self.body.set_focus(len(self.body)-1)
        except:
            pass

    def set_focus_top(self):
        self.body.set_focus(0)


class MyAttrMap(urwid.AttrMap):
    def __init__(self,w,attr_map,focus_map=None):
        super(MyAttrMap,self).__init__(w,attr_map,focus_map)

    def __getattribute__(self,name):
        try:
            return super(MyAttrMap,self).__getattribute__(name)
        except:
            return self.original_widget.__getattribute__(name)


class MyLineBox(urwid.LineBox):
    def __init__(self,original_widget):
        super(MyLineBox,self).__init__(original_widget)

    def __getattribute__(self,name):
        try:
            return super(MyLineBox,self).__getattribute__(name)
        except:
            return self.original_widget.__getattribute__(name)


class SelectableText(urwid.Text):
    def __init__(self,text):
        super(SelectableText,self).__init__(text)

    def selectable(self):
        return True
    
    def keypress(self,size,key):
        return key


##############################################################################
# composition
#
# +----ChatView(urwid.Columns)---------------------------------------------+
# | +--urwid.Pile-------------+ +--ChatFrame(urwid.Frame)----------------+ | 
# | | +--urwid.ListBox------+ | | +--urwid.Text------------------------+ | |
# | | | +-----------------+ | | | |  chattitle                         | | |
# | | | | chatname        | | | | +------------------------------------+ | |
# | | | +-----------------+ | | | +--ChatListBox(urwid.ListBox)--------+ | |
# | | | |                 | | | | | +--urwid.Pile--------------------+ | | |
# | | | +-----------------+ | | | | | username                  date | | | |
# | | |                     | | | | |--------------------------------+ | | |
# | | |                     | | | | | message                   date | | | |
# | | |                     | | | | +--------------------------------+ | | |
# | | |                     | | | | | message                   date | | | |
# | | |                     | | | | +--------------------------------+ | | |
# | | +---------------------+ | | | |                                | | | |
# | +-------------------------+ | | |                                | | | |
# | | +--urwid.ListBox------+ | | | |                                | | | |
# | | | +-----------------+ | | | | |                                | | | |
# | | | | username/status | | | | | +--------------------------------+ | | |
# | | | +-----------------+ | | | |                                    | | |
# | | | |                 | | | | |                                    | | |
# | | | +-----------------+ | | | |                                    | | |
# | | |                     | | | |                                    | | |
# | | |                     | | | |                                    | | |
# | | |                     | | | |                                    | | |
# | | |                     | | | +------------------------------------+ | |
# | | |                     | | | +--ChatInput(urwid.Edit)-------------+ | |
# | | |                     | | | |                                    | | |
# | | +---------------------+ | | +------------------------------------+ | |
# | +-------------------------+ +----------------------------------------+ |
# +------------------------------------------------------------------------+
#
# chatname 
# +-urwid.Columns----------------------------------------------------+
# | number(urwid.Text) | unread flag(urwid.Text) | title(urwid.Text) |
# +------------------------------------------------------------------+
#
# username/status
# +-urwid.Columns-----------------------------+
# | username(urwid.Text) | status(urwid.Text) |
# +-------------------------------------------+
#
# username/date
# +-urwid.Columns---------------------------+
# | username(urwid.Text) | date(urwid.Text) |
# +-----------------------------------------+
#
# message/date
# +-urwid.Columns---------------------------------------+
# | message(ChatMessage(urwid.Text)) | date(urwid.Text) |
# +-----------------------------------------------------+
#

class ChatListBox(MyListBox):
    def __init__(self):
        body = urwid.SimpleListWalker([])
        self.prev_name = None
        self.prev_date = None
        super(ChatListBox,self).__init__(body)

    def append_message(self,name,date,message):
        name_ = name.get_text()
        date_ = date.get_text()
        if self.prev_name != name_:
            self.prev_name = name_
            self.prev_date = date_
            name_and_date = urwid.Columns([name,('fixed',11,date)])
            # copy
            date = urwid.AttrMap(urwid.Text(date.get_text()),\
                                                date.get_attr_map())
            self.body.append(name_and_date)
        if date_ == self.prev_date:
            date.set_attr_map({None:"invisible"})
        else:
            self.prev_date = date_
        message = urwid.Columns([message,('fixed',11,date)])
        self.body.append(message)

        self.set_focus_bottom()


class ChatMessage(SelectableText):
    def __init__(self,text):
        super(ChatMessage,self).__init__(text)

    def keypress(self,size,key):
        if key == 'enter':
            self.open_url(self.text)
        else:
            return key

    def open_url(self,message):
        urlpattern = re.compile(r"""
      (
        (
          (
            [0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|   #IPAdress
            (
              (
                ((news|telnet|nttp|file|http|ftp|https)://)|  #Scheme
                (www|ftp)[-A-Za-z0-9]*\.                      #HostName 
              )
              ([-A-Za-z0-9\.]+)                               #HostName 
            )
          )
          (:[0-9]*)?                                          #Port
        )
          (
            /[-A-Za-z0-9_\$\.\+\!\*\(\),;:@&=\?/~\#\%]*|      #Path
          )   
      )
      """,re.VERBOSE)

        urls = urlpattern.findall(message)
        if urls:
            for url in urls:
                try:
                    webbrowser.open(url[0])
                except:
                    pass



class ChatFrame(urwid.Frame):
    def __init__(self,body,header=None,footer=None,focus_part='footer'):
        self.chattitle = header
        self.chatlist = body
        self.chatinput = footer
        super(ChatFrame,self).__init__(MyLineBox(body), \
                MyLineBox(header),MyLineBox(footer),focus_part)

    def keypress(self,size,key):
        if self.get_focus() == 'body':
            if key == 'i':
                self.set_focus('footer')
            else:
                return super(ChatFrame,self).keypress(size,key)
        elif self.get_focus() == 'footer':
            if key == 'down':
                self.set_focus('body')
                self.chatlist.keypress(size,'down')
            elif key == 'up':
                self.set_focus('body')
                self.chatlist.keypress(size,'up')
            else:
                return super(ChatFrame,self).keypress(size,key)
        else:
            return super(ChatFrame,self).keypress(size,key)

    def get_focus(self):
        return self.focus_part

    def set_chatlist(self,chatlist):
        self.chatlist = chatlist
        self.set_body(MyLineBox(chatlist))


class ChatInput(urwid.Edit):
    def __init__(self,caption,edit_text):
        super(ChatInput,self).__init__(caption,edit_text)
        self.word = re.compile(r"\w+\s*$",re.UNICODE)

    def keypress(self,size,key): 
        if key == 'ctrl u':
            text = self.get_edit_text()[self.edit_pos:]
            self.set_edit_text(text)
            self.set_edit_pos(0)
        elif key == 'ctrl k':
            text = self.get_edit_text()[:self.edit_pos]
            self.set_edit_text(text)
        elif key == 'ctrl w': 
            pos = self.edit_pos
            text = self.get_edit_text()
            text_ = text[:pos]
            new_pos = self.word.search(text_)
            if new_pos != None:
                new_pos = new_pos.start()
                text = text[:new_pos] + text[pos:]
                self.set_edit_text(text)
                self.set_edit_pos(new_pos)
        elif key == 'ctrl d':
            super(ChatInput,self).keypress(size,'delete')
        elif key == 'ctrl b':
            super(ChatInput,self).keypress(size,'left')
        elif key == 'ctrl f':
            super(ChatInput,self).keypress(size,'right')
        elif key == 'ctrl a':
            super(ChatInput,self).keypress(size,'home')
        elif key == 'ctrl e':
            super(ChatInput,self).keypress(size,'end')
        else:
            super(ChatInput,self).keypress(size,key)


class ChatView(urwid.Columns):
    def __init__(self,pepi):
        self.blank = re.compile(r"^\s*$")
        self.pepi = pepi
        self.skypechats = pepi.skypechats
        self.chatlists  = pepi.chatlists
        self.chatnames = pepi.chatnames
        self.chatmembers_list = pepi.chatmembers_list
        self.user_list = MyLineBox(MyListBox(pepi.user_listwalker))

        self.chatmembers = self.chatmembers_list[0]
        self.currentchat_num = 0
        self.currentchat = self.skypechats[self.currentchat_num]
        self.chattitle = MyAttrMap(\
                urwid.Text(self.currentchat.FriendlyName),"title")
        self.chatinput = ChatInput("> ","")
        self.chatframe = ChatFrame(self.chatlists[self.currentchat_num],\
                header=self.chattitle,footer=self.chatinput)
        self.chatinfo = urwid.Pile([self.chatnames,self.chatmembers])
        # 1:3
        super(ChatView,self).__init__([("weight",1,self.chatinfo),\
                ("weight",3,self.chatframe)])
        self.set_focus_chatframe()
        self.chatframe.chatlist.set_focus_bottom()
        self.set_chatname_attr(0,0)

    def keypress(self,size,key):
        focus = self.get_focus()
        chatframe_focus = self.chatframe.get_focus()
        if key == 'esc':
            self.chatframe.set_focus('body')
        elif key == 'ctrl n':
            new_num = (self.currentchat_num+1) % len(self.skypechats)
            self.change_chat(new_num)
        elif key == 'ctrl p':
            new_num = self.currentchat_num-1
            if new_num < 0:
                new_num = len(self.skypechats)-1
            self.change_chat(new_num)
        elif chatframe_focus == 'footer':
            if key == 'enter':
                message = self.chatinput.get_edit_text()
                if not self.blank.match(message):
                    self.send_message(message)
                self.chatinput.set_edit_text("")
            return super(ChatView,self).keypress(size,key)
        else:
            if key == 'l':
                self.set_focus_chatframe()
            elif key == 'i':
                self.set_focus_chatframe()
                self.chatframe.set_focus('footer')
            elif key == 'c':
                self.set_focus_chatname()
            elif key == 'u':
                self.change_chatmember_display(self.user_list)
                self.set_focus_chatmember()
            elif key == 'm':
                self.change_chatmember_display(self.chatmembers)
                self.set_focus_chatmember()
            elif key in ('0','1','2','3','4','5','6','7','8','9'):
                key = int(key)
                if key < len(self.skypechats):
                    self.change_chat(key)
            elif focus == self.chatinfo:
                focus = focus.get_focus()
                if focus == self.chatnames:
                    if key == 'enter':
                        self.change_chat(focus.get_focus()[1]/2)
                    else:
                        return super(ChatView,self).keypress(size,key)
                else:
                    if key == 'enter':
                        # create chat
                        user = focus.get_focus()[0]
                        self.pepi.create_chat_with(user)
                    else:
                        return super(ChatView,self).keypress(size,key)
            else:
                return super(ChatView,self).keypress(size,key)


    def send_message(self,message):
        self.currentchat.SendMessage(message)
        name = urwid.Text(self.pepi.myname)
        name = MyAttrMap(name,"me")
        date = datetime.datetime.today().strftime("%m-%d %H:%M")
        date = urwid.Text(date)
        date = MyAttrMap(date,"me")
        message = ChatMessage(message)
        message = MyAttrMap(message,None,"reveal focus")
        self.chatframe.chatlist.append_message( name,date,message)
        self.redraw()

    def set_chatname_attr(self,old,new):
        self.chatnames.body[old].set_attr_map(\
                                                  {None:'bg'})
        self.chatnames.body[new].set_attr_map(\
                                        {None:'current_chat'})

    def change_chat(self,new):
        old = self.currentchat_num
        self.currentchat_num = new
        self.set_chatname_attr((old*2),(new*2))
        self.currentchat = self.skypechats[new]
        self.chatframe.set_chatlist(self.chatlists[new])
        self.chatframe.chatlist.set_focus_bottom()
        self.chattitle.set_text(self.currentchat.FriendlyName)
        self.chatmembers = self.chatmembers_list[self.currentchat_num]

        # erase unread flag
        chatname = self.chatnames.body[new*2]
        if self.get_chatmembers_display() != self.user_list:
            self.change_chatmember_display(self.chatmembers)
        chatname.widget_list[1].set_text(" ")

        self.chatnames.set_focus(new*2)
        self.pepi.loop.draw_screen()

    def change_chatmember_display(self,widget):
        self.widget_list[0].widget_list[1] = widget
        self.pepi.loop.draw_screen()

    def set_focus_chatname(self):
        self.set_focus(0)
        self.widget_list[0].set_focus(0)

    def set_focus_chatmember(self):
        self.set_focus(0)
        self.widget_list[0].set_focus(1)

    def set_focus_chatframe(self):
        self.set_focus(1)

    def get_chatmembers_display(self):
        return self.widget_list[0].widget_list[1]
    
    def redraw(self):
        self.pepi.loop.draw_screen()

class Pepi():
    def __init__(self):
        self.skype = Skype4Py.Skype()
#        self.start_skype()
        self.skype.Attach()
        self.get_chat()
        self.myname = self.get_myname()
        self.make_userlist()
        self.make_chatlist()
        self.make_chatnamelist()
        self.make_view()
        self.set_callback_func()

    def start_skype(self):
        if not self.skype.Client.IsRunning:
            self.skype.Client.Start()
            while not self.skype.Client.IsRunning:
                time.sleep(2)

    def get_chat(self):
        self.skypechats = []
        # ActiveChats[0].Name contains all active chat name, probably bug..
        chatnames = self.skype.ActiveChats[0].Name.split(' ')
        chatnames = sorted(set(chatnames),key=chatnames.index)
        self.skypechats = [Skype4Py.chat.Chat(self.skype,c) \
                                        for c in chatnames]
    
    def get_myname(self):
        return self.skype.CurrentUserProfile.FullName

    def make_userlist(self):
        def append_member(index,handle,name,status):
            if name == self.myname:
                attr = "me"
            else:
                attr = self.attrs[index%len(self.attrs)]
            name_ = MyAttrMap(SelectableText(name),attr,"reveal focus")
            status_ = MyAttrMap(urwid.Text(status),status)
            member = urwid.Columns([name_,("fixed",7,status_)])
            self.user_list.update({handle:[member,name_,status_]})
            self.user_listwalker.append(member)

        # user_list -> {handle:[urwid.Text(fullname),urwid.Text(status]}
        self.user_list = {}
        self.user_listwalker = urwid.SimpleListWalker([])
        self.chatmembers_list = []
        self.attrs = ["other1","other2","other3","other4","other5","other6"]
        for i,member in enumerate(sorted(\
                self.skype.Friends,key=lambda x:x.FullName)):
            handle = member.Handle
            name = member.FullName
            status = member.OnlineStatus
            if name == "":
                name = handle
            append_member(i,handle,name,status)

        for chat in self.skypechats: 
            members = urwid.SimpleListWalker([])
            for member in chat.Members:
                status = member.OnlineStatus
                handle = member.Handle
                name = member.FullName
                if name == "":
                    name = handle
                if not self.user_list.has_key(handle):
                    # someone not my friend
                    append_member(0,handle,name,status)
                members.append(self.user_list[handle][0])
            self.chatmembers_list.append(MyLineBox(MyListBox(members)))

    def make_chatlist(self):
        self.chatlists = []
        for i in xrange(len(self.skypechats)):
            self.chatlists.append(ChatListBox())
#            for message in self.skypechats[i].RecentMessages:
#                self.append_message(message,i)

    def make_chatnamelist(self):
        self.chatnames = urwid.SimpleListWalker([])
        for i in xrange(len(self.skypechats)):
            # chatnumber,read flag,chatname
            chatname = urwid.Columns([\
                    ("fixed",len(str(i))+1,urwid.Text(str(i))),\
                    ("fixed",1,urwid.Text(" ")),\
                    SelectableText(self.skypechats[i].FriendlyName)])
            self.chatnames.append(MyAttrMap(chatname,'bg',"reveal focus"))
            self.chatnames.append(urwid.Divider('-'))
        self.chatnames = MyLineBox(MyListBox(self.chatnames))

    def make_view(self):
        self.palette = [
                # name          , foreground color , background color
                ('bg'           , 'light gray'     , 'black' )        , 
                ('reveal focus' , 'dark cyan'      , 'light red')     , 
                ('invisible'    , 'black'          , 'black' )        , 
                ('exit'         , 'dark red'       , 'black' )        , 
                ('title'        , 'dark green'     , 'black' )        , 
                ('me'           , 'light red'      , 'black' )        , 
                ('other1'       , 'dark cyan'      , 'black' )        , 
                ('other2'       , 'light magenta'  , 'black' )        , 
                ('other3'       , 'light green'    , 'black' )        , 
                ('other4'       , 'light blue'     , 'black' )        , 
                ('other5'       , 'dark red'       , 'black' )        , 
                ('other6'       , 'brown'          , 'black' )        , 
                ('current_chat' , 'dark green'     , 'black' )        , 
                ('unread'       , 'dark cyan'      , 'black' )        , 
                ('ONLINE'       , 'light red'      , 'black' )        , 
                ('SKYPEME'      , 'light red'      , 'black' )        , 
                ('AWAY'         , 'light blue'     , 'black' )        , 
                ('NA'           , 'light blue'     , 'black' )        , 
                ('DND'          , 'light blue'     , 'black' )        , 
                ('INVISIBLE'    , 'light gray'     , 'black' )        , 
                ('OFFLINE'      , 'light gray'     , 'black' )        , 
                ]
        self.view = ChatView(self)
        self.view = MyAttrMap(self.view,'bg')
        fonts = urwid.get_all_fonts()
        for name, fontcls in fonts:
            font = fontcls()
            if fontcls == urwid.Thin6x6Font:
                exit = urwid.BigText(('exit'," Quit?"), font)
                self.exit_view = urwid.Overlay(\
                        exit,self.view,'center',None,'middle',None)
                break
        else:
            exit = urwid.Filler(urwid.Text(("exit","Quit?")),'top')
            self.exit_view = urwid.Overlay(\
                    exit,self.view,'center',10,'middle',1)

    def set_callback_func(self):
        self.skype.OnMessageStatus = self.OnMessageStatus
        self.skype.OnOnlineStatus = self.OnOnlineStatus
        self.skype.OnChatMembersChanged = self.OnChatMembersChanged

    def main(self):
        self.loop = urwid.MainLoop(self.view,self.palette,\
                unhandled_input=self.unhandled_input)
        self.loop.screen.set_terminal_properties(colors=256)
        self.loop.run()

    def unhandled_input(self,key):
        if key == 'q':
            self.loop.widget = self.exit_view
        elif self.loop.widget == self.exit_view:
            if key in ('y', 'Y'):
                raise urwid.ExitMainLoop()
            else:
                self.loop.widget = self.view

    def append_message(self,message,index):
        name = self.user_list[message.Sender.Handle][1]
        attr = name.get_attr_map()
        date = message.Datetime.strftime("%m-%d %H:%M")
        date = urwid.Text(date)
        date = MyAttrMap(date,attr)
        mes  = ChatMessage(message.Body)
        mes  = MyAttrMap(mes,None,"reveal focus")
        self.chatlists[index].append_message(name,date,mes)

    def append_chat(self,chat):
       self.skypechats.append(chat)
       self.chatlists.append(ChatListBox())
#       for message in chat.RecentMessages:
#           self.append_message(message,-1)
       chatname = urwid.Columns([\
               ("fixed",len(str((len(self.skypechats)-1)))+1,\
                urwid.Text(str(len(self.skypechats)-1))),\
               ("fixed",1,urwid.Text(" ")),\
               urwid.Text(chat.FriendlyName)])
       self.chatnames.body.append(\
               MyAttrMap(chatname,'bg',None))
       self.chatnames.body.append(urwid.Divider('-'))

       members = urwid.SimpleListWalker([])
       self.chatmembers_list.append(MyLineBox(MyListBox(members)))
       self.append_member(chat,chat.Members)

    def append_member(self,chat,users):
        index = self.skypechats.index(chat)
        chatmembers = self.chatmembers_list[index]
        chatmembers = chatmembers.body
        for user in users:
            handle = user.Handle
            name = user.FullName
            status = user.OnlineStatus
            if name == "":
                name = handle
            for current_member in chatmembers:
                name_ =  current_member.widget_list[0].get_text()[0]
                if name == name_:  # already exists
                    break  
            else:
                if self.user_list.has_key(handle):
                    chatmembers.append(self.user_list[handle][0])
                else:
                    name_ = urwid.Text(name)
                    status = user.OnlineStatus
                    status_ = MyAttrMap(urwid.Text(status),status)
                    member = urwid.Columns([name_,\
                            ("fixed",len(status),status_)])
                    self.user_list.update( {handle:[\
                            len(self.user_listwalker),name_,status_]})
                    self.user_listwalker.append(member)
                    chatmembers.append(self.user_listwalker[-1])

    def create_chat_with(self,user):
        for key,value in self.user_list.iteritems():
            if value[0] == user:
                self.skype.CreateChatWith(key)
                return
            

    def OnMessageStatus(self,message,status):
        if status == 'RECEIVED' and message.Body != "":
            if message.Chat not in self.skypechats:
                self.append_chat(message.Chat)

            index = self.skypechats.index(message.Chat)
            self.append_message(message,index)
            if message.Chat != self.view.currentchat:
                # set unread flag
                chatname = self.chatnames.body[index*2]
                chatname.widget_list[1].set_text("*")
                chatname.set_attr_map({None:"unread"})
            self.loop.draw_screen()

    def OnChatMembersChanged(self,chat,users):
        if chat not in self.skypechats:
            self.append_chat(chat)
        self.append_member(chat,users)

        self.loop.draw_screen()

    def OnOnlineStatus(self,user,status):
        handle = user.Handle
        self.user_list[handle][2].set_text(status)
        self.user_list[handle][2].set_attr_map({None:status})
        self.loop.draw_screen()


if __name__ == '__main__':
    Pepi().main()


# vim: set et ts=4 sts=4 sw=4 :
