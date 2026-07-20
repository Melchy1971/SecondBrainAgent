# v31.69 Tray Approval Action

The Jarvis tray menu now provides a direct action for opening the native
approval view. It restores the desktop window and navigates through the
existing application view router.

The tray callback is marshalled onto the Tk event loop and does not read or
mutate approval data itself.
