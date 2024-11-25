from django.core.management import call_command


def dbbackup_func():
    try:
        call_command("dbbackup")
    except:
        pass
