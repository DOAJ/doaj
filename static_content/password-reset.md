---
layout: sidenav
fragment: false
title: Forgot your password
toc: true
sticky_sidenav: true
highlight: false
---

Please provide your username or e-mail address to reset your password.

<form action="{{ site.baseurl }}{% link login.md %}">
  <div class="form__question">
    <label for="email">E-mail address or username</label>
    <input id="email" type="email">
  </div>
  <p>
    <input type="submit" value="Reset password">
  </p>
</form>
