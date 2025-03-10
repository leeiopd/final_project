from django.shortcuts import render, redirect, get_object_or_404
from .models import Profile
from movies.models import Genre, Review
from .forms import CreateForm, LoginForm, ProfileForm
from django.contrib.auth import get_user_model, authenticate, logout
from django.contrib.auth import login as user_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Avg

# Create your views here.

@require_http_methods(['GET'])
def userInfo(request, user_id):
    user_info = get_object_or_404(get_user_model(), pk=user_id)
    context = {'user_info':user_info}
    return render(request, 'accounts/info.html', context)

@require_http_methods(['GET', 'POST'])
def signup(request):
    if request.user.is_authenticated:
        return redirect('movies:main')
    else:
        if request.method == 'POST':
            userform = CreateForm(request.POST)
            if userform.is_valid():
                user = userform.save()
                Profile.objects.create(user=user, point=0)
                user_login(request, user)
                return redirect('accounts:updateUser')
        else:
            userform = CreateForm()
        context = {'userform': userform}
        return render(request, 'accounts/signup.html', context)
        

@require_http_methods(['GET', 'POST'])
@login_required
def updateUser(request):
    if request.method == 'POST':
        userProfileform = ProfileForm(request.POST, instance=request.user.profile)
        if userProfileform.is_valid():
            userProfileform.save()
            return redirect('accounts:proflieTogenre')
    else:
        userProfileform = ProfileForm(instance=request.user.profile)
    context = {'userProfileform':userProfileform}
    return render(request, 'accounts/profile.html', context)

@login_required
def proflieTogenre(request):
    return render(request, 'accounts/profileTogenre.html')


@require_http_methods(['GET', 'POST'])
@login_required
def updateGenre(request):
    user = get_object_or_404(get_user_model(), pk=request.user.pk)
    if request.method == 'POST':
        allGenre = Genre.objects.all()

        for genre in allGenre:
            if user in genre.like_users.all():
                genre.like_users.remove(user)

        like_genres = request.POST.getlist('genres')
        for genreId in like_genres:
            like_genre = get_object_or_404(Genre, pk=genreId)
            like_genre.like_users.add(user)

        user_genres = user.like_genres.all()
        context = {'user_genres': user_genres}
        return redirect('accounts:user_info', user.pk)
    else:
        user_genres = user.like_genres.all()
        context = {'user_genres': user_genres}
        return render(request, 'accounts/updateGenres.html', context)


@require_http_methods(['GET', 'POST'])
def login(request):
    if request.user.is_authenticated:
        return redirect('movies:main')
    else:
        if request.method == 'POST':
            userLoginform = AuthenticationForm(request, request.POST)
            if userLoginform.is_valid():
                user_login(request, userLoginform.get_user())
                return redirect('movies:main')
        else:
            userLoginform = AuthenticationForm()
        context = {'userLoginform':userLoginform}
        return render(request, 'accounts/signin.html', context)

@require_http_methods(['GET'])
@login_required
def log_out(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def subscribe(request, user_id):
    if request.is_ajax():
        User = get_user_model()
        target_user = get_object_or_404(User, pk=user_id)
        
        if request.user in target_user.subscribers.all():
            target_user.subscribers.remove(request.user)
            is_subscribe = False
        else:
            target_user.subscribers.add(request.user)
            is_subscribe = True
        return JsonResponse({'is_subscribe':is_subscribe, 'subscribe_count':target_user.subscribers.count()})



@login_required
def subscribeList(request, user_id):
    profiles = Profile.objects.all().order_by('-point')
    user_info = get_object_or_404(get_user_model(), pk=user_id)
    subscribes = user_info.subscribes.all()
    context = {'subscribes': subscribes, 'user_info':user_info, 'profiles':profiles}
    return render(request, 'accounts/subscribes.html', context)


@login_required
def subscriberList(request, user_id):
    profiles = Profile.objects.all().order_by('-point')
    user_info = get_object_or_404(get_user_model(), pk=user_id)
    subscribers = user_info.subscribers.all()
    context = {'subscribers':subscribers, 'user_info':user_info, 'profiles':profiles}
    return render(request, 'accounts/subscribers.html', context)




@login_required
def viewfeed(request, user_id):
    if request.user.id == user_id:
        user_info = get_object_or_404(get_user_model(), pk=user_id)
        # feeds = user.subscribe.prefetch_related('review_set')
        subscribes = user_info.subscribes.values_list('id')
        feeds = Review.objects.filter(user_id__in=subscribes).order_by('-id')
        # feeds = []
        # for user in allSubUser:
        #     feeds.append(user.review_set.all())

        context = {'feeds': feeds, 'user_info':user_info}
        return render(request, 'accounts/feed.html', context)
    else:
        return redirect('movies:main')


@login_required
def favoritesDirectors(request, user_id):
    user_info = get_object_or_404(get_user_model(), pk=user_id)
    directors = user_info.like_directors.all()
    director_movie_lists=[]
    for director in directors:
        director_movies=[director]
        director_movies.append(director.movie_set.annotate(score_avg=Avg('review__score')).order_by('-score_avg')[:4])
        director_movie_lists.append(director_movies)
    context = {'director_movie_lists': director_movie_lists, 'user_info':user_info, 'directors': directors}
    return render(request, 'accounts/directors.html', context)


@login_required
def favoritesCasts(request, user_id):
    user_info = get_object_or_404(get_user_model(), pk=user_id)
    casts = user_info.like_casts.all()
    cast_movie_lists=[]
    for cast in casts:
        cast_movies=[cast]
        cast_movies.append(cast.movies.annotate(score_avg=Avg('review__score')).order_by('-score_avg')[:4])
        cast_movie_lists.append(cast_movies)
    context = {'cast_movie_lists': cast_movie_lists, 'user_info':user_info, 'casts': casts}
    return render(request, 'accounts/casts.html', context)


@login_required
def favoritesGenres(request, user_id):
    user_info = get_object_or_404(get_user_model(), pk=user_id)
    genres = user_info.like_genres.all()
    genre_movie_lists=[]
    for genre in genres:
        genre_movies=[genre]
        genre_movies.append(genre.movies.annotate(score_avg=Avg('review__score')).order_by('-score_avg')[:4])
        genre_movie_lists.append(genre_movies)
    context = {'genre_movie_lists': genre_movie_lists, 'user_info':user_info, 'genres': genres}
    return render(request, 'accounts/genres.html', context)


@login_required
def favoritesMovies(request, user_id):
    user_info = get_object_or_404(get_user_model(), pk=user_id)
    movies = user_info.like_movies.all()
    context = {'movies': movies, 'user_info':user_info}
    return render(request, 'accounts/movies.html', context)



@login_required
def reviewsList(request, user_id):
    user_info = get_object_or_404(get_user_model(), pk=user_id)
    reviews = user_info.review_set.order_by('-id')

    context = {'reviews': reviews, 'user_info':user_info}
    return render(request, 'accounts/reviews.html', context)

@login_required
def rank(request):
    profiles = Profile.objects.all().order_by('-point')
    user_info = get_object_or_404(get_user_model(), pk=request.user.id)
    context = {'profiles':profiles, 'user_info':user_info}
    return render(request, 'accounts/rank.html', context)