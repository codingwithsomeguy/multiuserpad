import os
import subprocess

from config import config


# maps from file extension to an action
KNOWN_EXECUTION_MODELS = {
    "c": "cd '%s' && gcc '%s' -o webinput -lm && ./webinput",
    "py": "cd '%s' && python3 '%s'",
    "js": "cd '%s' && node '%s'",
    # TODO: change classname from Default with multi-file-handling
    "java": "cd '%s' && javac '%s' && java Default",
    "cs": "cd '%s' && mcs '%s' && mono autosrc.exe",
}


def get_autosave_filename():
    as_filename = "autosrc.%s" % config.CODE_EXTENSION
    autosave_file = os.path.join(config.CODE_DIR, as_filename)
    return autosave_file


def do_save(text):
    # TODO: use a real temp file?
    autosave_file = get_autosave_filename()
    # TODO: take this from the autosave filename
    os.makedirs(config.CODE_DIR, exist_ok=True)
    open(autosave_file, "w").write(text)
    return autosave_file


def executor(text):
    temp_filename = do_save(text)
    temp_filepart = os.path.split(temp_filename)[1]
    # TODO: check which env to do based on extension passed in
    #   or the session / need some variables
    selected_model = "py"
    if config.CODE_EXTENSION in KNOWN_EXECUTION_MODELS:
        selected_model = config.CODE_EXTENSION
    cmd_pattern = KNOWN_EXECUTION_MODELS[selected_model]
    # assume we're in the same directory
    cmd = cmd_pattern % (config.CODE_DIR, temp_filepart)
    sub_pipe = subprocess.Popen(
        cmd, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    sub_pipe_stdout, sub_pipe_stderr = sub_pipe.communicate()

    stdout = sub_pipe_stdout.decode(config.HOST_ENCODING)
    stderr = sub_pipe_stderr.decode(config.HOST_ENCODING)

    return stdout, stderr
