---
layout: no-sidenav
fragment: false
title: Login
toc: true
highlight: false
---

DOAJ is free to use without logging in.

You only need an account if you have a journal in DOAJ or you are a volunteer.

<form action="{{ site.baseurl }}{% link dashboard/index.md %}">
  <div class="form__question">
    <label for="email">E-mail address or username</label>
    <input id="email" type="email">
  </div>
  <div class="form__question">
    <label for="password">Password</label>
    <input id="password" type="password">
  </div>
  <p>
    <input type="submit" value="Login">
  </p>
</form>

If you cannot log in, [reset your password]({{ site.baseurl }}{% link password-reset.md %}). If you still cannot login, [contact us]({{ site.baseurl }}contact/).
