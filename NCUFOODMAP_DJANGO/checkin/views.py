from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Checkin
from .forms import CheckinForm

@login_required
def checkin_create(request):
    if request.method == 'POST':
        form = CheckinForm(request.POST, request.FILES)
        if form.is_valid():
            checkin = form.save(commit=False)
            checkin.user = request.user
            checkin.save()
            messages.success(request, '美食打卡成功！')
            return redirect('checkin_detail', pk=checkin.pk)
    else:
        form = CheckinForm()
    return render(request, 'checkin/checkin_form.html', {'form': form})

@login_required
def checkin_detail(request, pk):
    checkin = get_object_or_404(Checkin, pk=pk, user=request.user)
    return render(request, 'checkin/checkin_detail.html', {'checkin': checkin})

@login_required
def checkin_update(request, pk):
    checkin = get_object_or_404(Checkin, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CheckinForm(request.POST, request.FILES, instance=checkin)
        if form.is_valid():
            form.save()
            messages.success(request, '打卡內容已更新！')
            return redirect('checkin_detail', pk=checkin.pk)
    else:
        form = CheckinForm(instance=checkin)
    return render(request, 'checkin/checkin_form.html', {'form': form, 'edit_mode': True})

@login_required
def checkin_delete(request, pk):
    checkin = get_object_or_404(Checkin, pk=pk, user=request.user)
    if request.method == 'POST':
        checkin.delete()
        messages.success(request, '打卡已刪除！')
        return redirect('checkin_create')
    return render(request, 'checkin/checkin_confirm_delete.html', {'checkin': checkin})

@login_required
def checkin_list(request):
    checkins = Checkin.objects.filter(user=request.user).order_by('-date', '-created_at')
    return render(request, 'checkin/checkin_list.html', {'checkins': checkins})

@login_required
def checkin_calendar(request):
    checkins = Checkin.objects.filter(user=request.user)
    # 轉換為 FullCalendar 需要的事件格式
    events = [
        {
            'title': f"{c.restaurant_name} - {c.item}",
            'start': c.date.strftime('%Y-%m-%d'),
            'url': f"/checkin/{c.pk}/"
        }
        for c in checkins
    ]
    return render(request, 'checkin/checkin_calendar.html', {'events': events}) 