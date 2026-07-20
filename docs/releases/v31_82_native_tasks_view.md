# v31.82 Native Tasks View

The Tkinter desktop shell now renders a live Tasks view from the root-local
persistent task store instead of falling through to the generic placeholder.
The view shows open, completed and total counts plus bounded recent task rows,
IDs, priorities and available German commands.

Task fields are length-bounded and stripped of control characters before
rendering. Provider failures return an unavailable state without exposing
exception details or local paths. Successful task actions automatically refresh
the active Tasks view.
