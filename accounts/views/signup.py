from django.contrib.auth import login
from django.shortcuts import redirect, render

from accounts.forms import SignupForm


def signup(request):
    if request.user.is_authenticated:
        return redirect("accounts:home")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:home")
    else:
        form = SignupForm()

    return render(request, "accounts/signup.html", {"form": form})
