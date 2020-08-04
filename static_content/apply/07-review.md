---
layout: apply
title: <span data-feather="eye" aria-hidden="true"></span> Review your answers
toc: true
fragment: false
highlight: false
number: 7
---

Please review your answers before submitting your application.

---

<table>
  <tr>
    <th>Open access compliance</th>
    <th><a href="{{ site.baseurl }}{% link apply/01-oa-compliance.md %}">Edit this section</a></th>
  </tr>
  {% for question in site.data.form-01-oa-compliance %}
  <tr>
    <td>{{ question.label }}</td>
    <td>
      {% if question.input == 'url' %}<a href='https://www.example.com' target='_blank'>{% endif %}
      Lorem ipsum dolor sit amet
      {% if question.input == 'url' %}</a>{% endif %}
    </td>
  </tr>
  {% endfor %}
</table>

---

<table>
  <tr>
    <th>About the journal</th>
    <th><a href="{{ site.baseurl }}{% link apply/02-about.md %}">Edit this section</a></th>
  </tr>
  {% for question in site.data.form-02-about %}
  <tr>
    <td>{{ question.label }}</td>
    <td>Lorem ipsum dolor sit amet</td>
  </tr>
  {% endfor %}
</table>

---

<table>
  <tr>
    <th>Copyright & licensing</th>
    <th><a href="{{ site.baseurl }}{% link apply/03-copyright-licensing.md %}">Edit this section</a></th>
  </tr>
  {% for question in site.data.form-03-copyright-licensing %}
  <tr>
    <td>{{ question.label }}</td>
    <td>
      {% if question.input == 'url' %}<a href='https://www.example.com' target='_blank'>{% endif %}
      Lorem ipsum dolor sit amet
      {% if question.input == 'url' %}</a>{% endif %}
    </td>
  </tr>
  {% endfor %}
</table>

---

<table>
  <tr>
    <th>Editorial</th>
    <th><a href="{{ site.baseurl }}{% link apply/04-editorial.md %}">Edit this section</a></th>
  </tr>
  {% for question in site.data.form-04-editorial %}
  <tr>
    <td>{{ question.label }}</td>
    <td>
      {% if question.input == 'url' %}<a href='https://www.example.com' target='_blank'>{% endif %}
      Lorem ipsum dolor sit amet
      {% if question.input == 'url' %}</a>{% endif %}
    </td>
  </tr>
  {% endfor %}
</table>

---

<table>
  <tr>
    <th>Business model</th>
    <th><a href="{{ site.baseurl }}{% link apply/05-business-model.md %}">Edit this section</a></th>
  </tr>
  {% for question in site.data.form-05-business-model %}
  <tr>
    <td>{{ question.label }}</td>
    <td>
      {% if question.input == 'url' %}<a href='https://www.example.com' target='_blank'>{% endif %}
      Lorem ipsum dolor sit amet
      {% if question.input == 'url' %}</a>{% endif %}
    </td>
  </tr>
  {% endfor %}
</table>

---

<table>
  <tr>
    <th>Best practice</th>
    <th><a href="{{ site.baseurl }}{% link apply/06-best-practice.md %}">Edit this section</a></th>
  </tr>
  {% for question in site.data.form-06-best-practice %}
  <tr>
    <td>{{ question.label }}</td>
    <td>
      {% if question.input == 'url' %}<a href='https://www.example.com' target='_blank'>{% endif %}
      Lorem ipsum dolor sit amet
      {% if question.input == 'url' %}</a>{% endif %}
    </td>
  </tr>
  {% endfor %}
</table>

---

<div class="form__question">
  <input id="review-1" name="review" type="checkbox">
  <label for="review-1">I’ve reviewed the answers to my application and confirm that the information provided is accurate and true.</label>
</div>

<div class="form__question">
  <input id="review-2" name="review" type="checkbox">
  <label for="review-2">I understand that, if the information is found to be not sufficient or incomplete, my application will not be considered.</label>
</div>

<p class="pager-buttons">
  <a href="{{ site.baseurl }}{% link apply/06-best-practice.md %}" class="pager-buttons__left">Previous</a>
  <a href="{{ site.baseurl }}{% link apply/thank-you.md %}" class="pager-buttons__right">Submit</a>
</p>
