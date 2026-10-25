from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib import messages 
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from .models import Room, Topic, Message
from .forms import RoomForm, UserForm

"""
rooms = [
    {'id': 1, 'name': 'Lets learn Python'},
    {'id': 2, 'name': 'Design with me'},
    {'id': 3, 'name': 'Frontend Stuffs'},
]

"""


# The login function 
def loginPage(request):
    """
    This function checks if user authenticated,
    sends user to home page, 
    If the user info is inputed(request.method == POST),
    store the username and passsword in corresponding variables

    set context content to login so you can call in template
    and make it an argument
    """
    page ='login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username) #User has builtin username var
        except:
            messages.error(request, "") # If anythin goes wrong show error message

        user = authenticate(username=username, password=password) # validate the user with username and password

        if user is not None: # if user exists, log them in and redirect home
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Username OR password doesnt exist") # Error message 

    context ={'page': page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    """
    logout function and 
    redirect home
    """
    logout(request)
    return redirect('home')

def registerPage(request):
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration')

    return render(request, 'base/login_register.html', {'form': form})


def home(request):
    """
    Function to render data from models to home page
    'Q' is imported from django.db.models
    topic__name enters topic table and extracts the name 
    icontains helps make the query link be case insensitive 
    """
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    context = {'rooms': rooms, "topics" : topics, "room_count": room_count,
               'room_messages':room_messages}
    return render(request, 'base/home.html', context)

def userProfile(request, pk):
    user = get_object_or_404(User, id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context ={'user':user, 'rooms':rooms, 'room_messages':room_messages,
              'topics':topics}
    return render(request, 'base/profile.html', context)


def room(request, pk):
    """
    room representation function 
    making pk the id value which is generated when a new room is created
    """
    room = get_object_or_404(Room, id=pk)
    room_messages = room.message_set.all().order_by('-created')
    participants = room.participants.all()

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect('login')

        message = Message.objects.create(
            user=request.user, 
            room=room, 
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)
    
    context = {'room': room, "room_messages": room_messages, 
               "participants": participants}
    return render(request, 'base/room.html', context)

@login_required(login_url="login") # decorator to restrict unauthorised users
def createRoom(request):
    """
    This function Creates a new room.
    
    """
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == "POST":
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('home')
    
    context = {'form':form, 'topics':topics}
    return render(request, 'base/room_form.html', context)

@login_required(login_url="login")
def updateRoom(request, pk):
    room = get_object_or_404(Room, id=pk)

    if request.user != room.host:
        raise PermissionDenied

    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.method == "POST":
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')
    context = {'form': form, 'topics':topics, 'room':room}
    return render(request, 'base/room_form.html', context)

@login_required(login_url="login")
def deleteRoom(request, pk):
    room = get_object_or_404(Room, id=pk)

    if request.user != room.host:
        raise PermissionDenied
    
    if request.method == "POST":
        room.delete()
        return redirect('home')
    return render(request, "base/delete.html", {"obj": room})

@login_required(login_url="login")
def deleteMessage(request, pk):
    message = get_object_or_404(Message, id=pk)

    if request.user != message.user:
        raise PermissionDenied
    
    if request.method == "POST":
        message.delete()
        return redirect('home')
    return render(request, "base/delete.html", {"obj": message})

@login_required(login_url="login")
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == "POST":
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
        
    return render(request, 'base/update_user.html', {'form':form})

def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {'topics': topics})


def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages': room_messages})