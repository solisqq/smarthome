import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from Network.server import SmartMessage

def index(request):
    return HttpResponse("Hello, world. You're at the smartmanage index.")

@csrf_exempt
def requests(request):
    try:
        data = json.loads(request.body)
        print(data)
        if data['type'] == 'request':
            if 'question' in data['msg'].keys() and data['msg']['question'] == 'isAvailable':
                return JsonResponse(SmartMessage.respond('host', data['uid'], "web",{"isAvailable": "True"}).msg)
            if 'test' in data['msg'].keys() and data['msg']['test'] == 'test':
                return JsonResponse(SmartMessage.respond('host', data['uid'], "web",{"test": "hehehe"}).msg)
        return 
    except:
        return JsonResponse({'response':'InvalidCommand'})