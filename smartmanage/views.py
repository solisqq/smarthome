import json

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from Network.server import SmartMessage
from django.views.decorators.http import require_POST
from Network.testclient import TestClient
import requests

hostSession = None

def index(request : HttpRequest):
    return render(request,"index.html")

@require_POST
@csrf_exempt
def trigger(request : HttpRequest, id : int):
    if request.method =='POST':
        print("Done", id, request.body)
        TestClient.json_message("test")
    return JsonResponse({"status":"ok"})

@csrf_exempt
def requestsf(request : HttpRequest):
    try:
        data = json.loads(request.body)
        print(data)
        hostSession = request.session
        hostSession.set_expiry(0)
        if data['type'] == 'request':
            if 'question' in data['msg'].keys() and data['msg']['question'] == 'isAvailable':
                return JsonResponse(SmartMessage.respond('host', data['uid'], "web",{"isAvailable": "True"}).msg)
            if 'test' in data['msg'].keys() and data['msg']['test'] == 'test':
                return JsonResponse(SmartMessage.respond('host', data['uid'], "web",{"test": "hehehe"}).msg)
            if 'trigger' in data.keys():
                print(data)
        return 
    except:
        return JsonResponse({'response':'InvalidCommand'})