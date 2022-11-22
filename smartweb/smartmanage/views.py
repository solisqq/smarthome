import json

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from controller.Network.JSONProtocol import JSONTalker, JSONPacket
from django.views.decorators.http import require_POST
import config

def handlePacket(packet : JSONPacket):
    if packet.type == JSONPacket.PING:
        JSONTalker.sendToController(JSONPacket.response("pong", packet))

hostSession = None
talker = JSONTalker(config.WebServer.ADDR, handlePacket)

def index(request : HttpRequest):
    return render(request,"index.html")

@require_POST
@csrf_exempt
def trigger(request : HttpRequest, id : int):
    wasSent = JSONTalker.sendToController(
        JSONPacket.trigger(str(id), 
        config.WebServer.NAME, 
        config.Controller.NAME))
    print(request.body, wasSent)
    if not wasSent: return JsonResponse({"status":"failed", "reason": "NoConnection"})
    return JsonResponse({"status":"ok", "reason":""})

@csrf_exempt
def requestsf(request : HttpRequest): pass
    # try:
    #     data = json.loads(request.body)
    #     print(data)
    #     hostSession = request.session
    #     hostSession.set_expiry(0)
    #     if data['type'] == 'request':
    #         if 'question' in data['msg'].keys() and data['msg']['question'] == 'isAvailable':
    #             return JsonResponse(SmartMessage.respond('host', data['uid'], "web",{"isAvailable": "True"}).msg)
    #         if 'test' in data['msg'].keys() and data['msg']['test'] == 'test':
    #             return JsonResponse(SmartMessage.respond('host', data['uid'], "web",{"test": "hehehe"}).msg)
    #         if 'trigger' in data.keys():
    #             print(data)
    #     return 
    # except:
    #     return JsonResponse({'response':'InvalidCommand'})