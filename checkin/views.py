from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import CheckinForm
from django.contrib.auth.models import User
from .models import Checkin
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime, date

# @login_required 暫時移出登入要求
def checkin_form(request):
    if request.method == 'POST':
        form = CheckinForm(request.POST, request.FILES)
        if form.is_valid():
            # 檢查該日是否已打卡
            date = form.cleaned_data['date']
            existing_checkin = Checkin.objects.filter(user=request.user, date=date).first()
            
            if existing_checkin:
                messages.warning(request, '該日期已經有打卡記錄了！')
                return redirect('checkin_form')
            
            checkin = form.save(commit=False)
            checkin.user = request.user
            checkin.save()
            messages.success(request, '打卡成功！')
            return redirect('calendar')
    else:
        form = CheckinForm()
    return render(request, 'checkin/checkin_form.html', {'form': form})

def calendar_view(request):
    # 只顯示 2025/05/06 的假資料
    fake_checkin = {
        'id': 1,
        'date': date(2025, 5, 6),
        'restaurant': '假資料餐廳',
        'item': '假資料餐點',
        'price': 100,
        'rating': 5,
        'emotion_tag': '開心',
        'comment': '這是測試用的假資料',
        'image': None
    }
    checkins = [fake_checkin]
    return render(request, 'checkin/calendar.html', {'checkins': checkins})

def new_checkin(request):
    if request.method == 'POST':
        form = CheckinForm(request.POST, request.FILES)
        if form.is_valid():
            date = form.cleaned_data['date']
            existing_checkin = Checkin.objects.filter(user=request.user, date=date).first()
            
            if existing_checkin:
                messages.warning(request, '該日期已經有打卡記錄了！')
                return redirect('new_checkin')
            
            checkin = form.save(commit=False)
            checkin.user = request.user
            checkin.save()
            messages.success(request, '打卡成功！')
            return redirect('calendar')
    else:
        form = CheckinForm()
    return render(request, 'checkin/new_checkin.html', {'form': form})

def edit_checkin(request, checkin_id):
    checkin = get_object_or_404(Checkin, id=checkin_id, user=request.user)
    if request.method == 'POST':
        form = CheckinForm(request.POST, request.FILES, instance=checkin)
        if form.is_valid():
            form.save()
            messages.success(request, '編輯成功！')
            return redirect('calendar')
    else:
        form = CheckinForm(instance=checkin)
    return render(request, 'checkin/edit_checkin.html', {'form': form, 'checkin': checkin})

def delete_checkin(request, checkin_id):
    checkin = get_object_or_404(Checkin, id=checkin_id, user=request.user)
    if request.method == 'POST':
        checkin.delete()
        messages.success(request, '刪除成功！')
        return redirect('calendar')
    return render(request, 'checkin/delete_confirm.html', {'checkin': checkin})

def checkin_detail(request, checkin_id):
    checkin = get_object_or_404(Checkin, id=checkin_id, user=request.user)
    return render(request, 'checkin/checkin_detail.html', {'checkin': checkin})
