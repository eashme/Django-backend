import os
from django.http import HttpResponse

# Create your views here.
from django.views.generic import View
from django.conf import settings

class PDFView(View):
    def get(self,request,pdf_name):

        f_byte = b''
        # 获取文件名
        file_name = "%s.pdf" % pdf_name

        if not file_name in os.listdir(settings.PDF_ROOT):
            return HttpResponse('路径错误!')

        with open(settings.PDF_ROOT +'/'+ file_name,'rb') as f:
            while True:
                con = f.read(1024)
                if not con:
                    break
                f_byte += con

        return HttpResponse(f_byte, content_type='application/pdf')
