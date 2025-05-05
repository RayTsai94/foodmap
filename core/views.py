from django.shortcuts import render, redirect

def home(request):
    return render(request, "index.html")

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        request.session['user'] = username
        return redirect('/')
    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    return redirect('/')

def calendar_page(request):
    return render(request, "calendar.html")

def checkin_new(request):
    return render(request, "checkin/checkin_form.html")  # 你可以先放個 hello 畫面測試