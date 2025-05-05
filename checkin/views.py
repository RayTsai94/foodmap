from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CheckinForm

# @login_required 暫時移出登入要求
def new_checkin(request):
    if request.method == 'POST':
        form = CheckinForm(request.POST, request.FILES)
        if form.is_valid():
            checkin = form.save(commit=False)
            checkin.user = User.objects.first()
            checkin.save()
            return redirect('/calendar/')  # 你要導去哪個頁面都可以改這裡
    else:
        form = CheckinForm()
    return render(request, 'checkin/new_checkin.html', {'form': form})
