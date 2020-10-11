# initial verison copied from: https://community.troikatronix.com/topic/6570/obs-osc-scene-switcher-my-version
# which was based on: https://github.com/CarloCattano/ObSC

import argparse
import logging
import sys
import os
from pythonosc import dispatcher
from pythonosc import osc_server

logging.basicConfig(level=logging.INFO)

sys.path.append('../')
from obswebsocket import obsws, requests  # noqa: E402

from dotenv import load_dotenv
load_dotenv()

host = os.getenv("HOST") or "localhost"
port = os.getenv("PORT") or 4444
password = os.getenv("PASSWORD") or "put_your_password_here"

print("Talking to OBS at '{0}:{1}'".format(host, port, password))

ws = obsws(host, port, password)
ws.connect()

ScenesNames = []
SceneSources = []

TransitionNames = []
TransitionSources = []


def sourceSwitch(source_name, scene, switch):
    ws.call(requests.SetSceneItemProperties(source_name, scene, visible=switch))


def is_integer(v):
    try:
        int(v)
        return True;
    except ValueError:
        return False;


def scene_switch(unused_addr, args, oscValue):
    try:
        if (is_integer(oscValue)):
            print(
                "CMD = '{0}' INDEX = {1} OBS SCENE NAME = '{2}'".format(args[0], oscValue, ScenesNames[int(oscValue)]))
            ws.call(requests.SetCurrentScene(ScenesNames[int(oscValue)]))
        else:
            print("OSC Value '{0}' cannot be converted to an integer.".format(oscValue))
    except:
        pass


def transition_switch(unused_addr, args, oscValue, timeValue=-1):
    print("Transition: '{0}', time: '{1}'".format(oscValue, timeValue))
    try:
        if (is_integer(oscValue)):
            if (int(timeValue) >= 0):
                print("CMD = '{0}' INDEX = {1} OBS TRANSITION NAME = '{2}', TIME = '{3}'"
                      .format(args[0], oscValue, TransitionNames[int(oscValue)], timeValue))
                ws.call(requests.SetCurrentTransition(TransitionNames[int(oscValue)]))
                ws.call(requests.SetTransitionDuration(int(timeValue)))
            else:
                print("CMD = '{0}' INDEX = {1} OBS TRANSITION NAME = '{2}'".format(args[0], oscValue,
                                                                                   TransitionNames[int(oscValue)]))
                ws.call(requests.SetCurrentTransition(TransitionNames[int(oscValue)]))

        else:
            print("OSC Value '{0}' cannot be converted to an integer.".format(oscValue))
    except:
        pass


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


if __name__ == "__main__":
    try:
        scenes = ws.call(requests.GetSceneList())
        for s in scenes.getScenes():
            name = s['name']
            print("Scene {0}: '{1}'".format(len(ScenesNames), name))
            ScenesNames.append(name)  # Add every scene to a list of scenes

        print("CURRENT SCENES IN OBS:\n", ScenesNames)

        transitions = ws.call(requests.GetTransitionList())
        for s in transitions.getTransitions():
            name = s['name']
            print("Transition {0}: '{1}'".format(len(TransitionNames), name))
            TransitionNames.append(name)  # Add every scene to a list of scenes

        print("CURRENT TRANSITIONS IN OBS:\n", TransitionNames)

        ### OSC SETTINGS
        parser = argparse.ArgumentParser()
        parser.add_argument("--ip", default="127.0.0.1", help="The ip to listen on")
        parser.add_argument("--port", type=int, default=5005, help="The port to listen on")

        args = parser.parse_args()  # parser for --ip --port arguments
        dispatcher = dispatcher.Dispatcher()

        dispatcher.map("/Transitions", list_transitions, "Transitions")
        dispatcher.map("/Scenes", list_scenes, "Scenes")
        dispatcher.map("/Scene", scene_switch, "Scene")  # OSC LISTENER
        dispatcher.map("/Transition", transition_switch, "Transition")  # OSC LISTENER

        server = osc_server.ThreadingOSCUDPServer((args.ip, args.port), dispatcher)
        print("Serving on {}".format(server.server_address))

        server.serve_forever()

    except KeyboardInterrupt:
        pass

    ws.disconnect()
