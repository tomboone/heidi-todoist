import azure.functions as func

from heidi_todoist.blueprint import bp

app = func.FunctionApp()

# Register the blueprint
app.register_functions(bp)
