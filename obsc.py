# initial verison copied from: https://community.troikatronix.com/topic/6570/obs-osc-scene-switcher-my-version
# which was based on: https://github.com/CarloCattano/ObSC

import argparse
import logging
import os
import sys
import threading

from dotenv import load_dotenv
from obswebsocket import obsws, requests, events
from pythonosc import dispatcher
from pythonosc import osc_server

logging.basicConfig(level=logging.INFO)

sys.path.append('../')

SceneNames = []
TransitionNames = []
CurrentScene = ""

def is_integer(v):
    try:
        int(v)
        return True;
    except ValueError:
        return False;

#
# Events that happened in OBS
#

def on_event(message):
    print(u"Got message: {}".format(message))

def on_switch(message):
    global CurrentScene
    CurrentScene = message.getSceneName()
    print(u"You changed the scene to {}".format(CurrentScene))

def on_source_renamed(message):
    print(u"You change the name of a scene from '{0}' to '{1}'".format(message.getPreviousname(), message.getNewname()))
    scene_index = SceneNames.index(message.getPreviousname())
    SceneNames[scene_index] = message.getNewname()

def on_transition_list_changed(message):
    print(u"Something changed in the transitions... new transitions")
    read_transitions_in_thread()

def on_source_created(message):
    print(u"You created new scene '{0}'".format(message.getSourcename()))
    read_scenes_in_thread()

def on_source_destroyed(message):
    print(u"You destroyed new scene '{0}'".format(message.getSourcename()))
    read_scenes_in_thread()

def on_source_order_changed(message):
    print(u"You destroyed new scene '{0}'".format(message.getSourcename()))
    read_scenes_in_thread()

def read_transitions_in_thread():
    t = threading.Thread(target=read_transitions)
    t.start()

def read_screnes_in_thread():
    t = threading.Thread(target=read_scenes)
    t.start()

#
# Requests from OCS client
#

def scene_switch(unused_addr, args, oscValue):
    try:
        if (is_integer(oscValue)):
            scene_name = SceneNames[int(oscValue)]
        else:
            scene_name = oscValue

        print("{0} '{1}'".format(args[0], scene_name))
        ws.call(requests.SetCurrentScene(scene_name))

    except:
        pass


def transition_switch(unused_addr, args, oscValue, timeValue = -1):
    try:
        if (is_integer(oscValue)):
            transition_name = TransitionNames[int(oscValue)]
        else:
            transition_name = oscValue

        if (is_integer(timeValue) and int(timeValue) >= 0):
            print("{0} '{1}' {2}".format(args[0], transition_name, timeValue))
            ws.call(requests.SetTransitionDuration(int(timeValue)))
            ws.call(requests.SetCurrentTransition(transition_name))
        else:
            print("{0} '{1}'".format(args[0], transition_name))
            ws.call(requests.SetCurrentTransition(transition_name))

    except:
        pass

#
# Get states from OBS
#

def list_scenes(unused_addr, args):
    scenes = ws.call(requests.GetSceneList())
    count = 0
    for s in scenes.getScenes():
        name = s['name']
        print("{0}: '{1}".format(count, name))
        count += 1

def list_transitions(unused_addr, args):
    transitions = ws.call(requests.GetTransitionList())
    count = 0
    for s in transitions.getTransitions():
        name = s['name']
        print("{0}: '{1}".format(count, name))
        count += 1

def read_transitions():
    global TransitionNames
    TransitionNames = []

    print("---------------------- TRANSITIONS ----------------------")
    transitions = ws.call(requests.GetTransitionList())
    for s in transitions.getTransitions():
        name = s['name']
        print("Transition {0}: '{1}'".format(len(TransitionNames), name))
        TransitionNames.append(name)  # Add every scene to a list of scenes

def read_scenes():
    global CurrentScene
    global SceneNames

    SceneNames = []

    try:
        print("----------------------   SCENES    ----------------------")
        scenes = ws.call(requests.GetSceneList())

        CurrentScene = scenes.getCurrentScene()
        print("Current Scene: '{0}'".format(CurrentScene))
        print()
        for s in scenes.getScenes():
            name = s['name']
            print("Scene {0}: '{1}'".format(len(SceneNames), name))
            SceneNames.append(name)  # Add every scene to a list of scenes
    except:
        pass

def read_settings(unused_addr):
    read_scenes()
    read_transitions()
    print("---------------------------------------------------------")


#
# main
#
if __name__ == "__main__":
    load_dotenv()

    # OBS host / port / password - we are the client
    obs_host = os.getenv("OBS_HOST") or "localhost"
    obs_port = os.getenv("OBS_PORT") or 4444
    obs_password = os.getenv("OBS_PASSWORD")

    print("Talking to OBS at '{0}:{1}'".format(obs_host, obs_port, obs_password))

    # OSC port / password - we are the server
    ocs_host = os.getenv("OCS_HOST") or "127.0.0.1"
    ocs_port = os.getenv("OCS_PORT") or 5005
    ocs_password = os.getenv("OCS_PASSWORD")        # not used yet

    # OSC SETTINGS
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default=ocs_host, help="The ip to listen on")
    parser.add_argument("--port", type=int, default=ocs_port, help="The port to listen on")

    ws = obsws(obs_host, obs_port, obs_password)
    ws.connect()

    try:
        read_settings("")

        args = parser.parse_args()  # parser for --ip --port arguments
        dispatcher = dispatcher.Dispatcher()

        ### listeners to OBS from the server ###
        # ws.register(on_event)    # uncomment when you want to watch all events (useful when adding new ones)
        ws.register(on_switch, events.SwitchScenes)
        ws.register(on_source_renamed, events.SourceRenamed)
        ws.register(on_transition_list_changed, events.TransitionListChanged)
        ws.register(on_source_created, events.SourceCreated)
        ws.register(on_source_destroyed, events.SourceDestroyed)
        ws.register(on_source_order_changed, events.SourceOrderChanged)

        ### listeners to OSC from the clients ###
        # list things in the terminal
        dispatcher.map("/scenes", list_scenes, "scenes")
        dispatcher.map("/transitions", list_transitions, "transitions")

        # do things in OBS
        dispatcher.map("/scene", scene_switch, "scene")  # OSC LISTENER
        dispatcher.map("/transition", transition_switch, "transition")  # OSC LISTENER

        server = osc_server.ThreadingOSCUDPServer((args.ip, args.port), dispatcher)
        print("Serving on {}".format(server.server_address))

        server.serve_forever()

    except KeyboardInterrupt:
        pass

    ws.disconnect()
