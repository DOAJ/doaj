---
layout: apply
title: Indonesia Accounting Journal
admin:  true
fragment: false
highlight: false
---


<table>
  <tr>
    <th>Open access compliance</th>
    <th><a href="{{ site.baseurl }}01-oa-compliance/">Edit this section</a></th>
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
    <th><a href="{{ site.baseurl }}02-about/">Edit this section</a></th>
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
    <th><a href="{{ site.baseurl }}03-copyright-licensing/">Edit this section</a></th>
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
    <th><a href="{{ site.baseurl }}04-editorial/">Edit this section</a></th>
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
    <th><a href="{{ site.baseurl }}05-business-model/">Edit this section</a></th>
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
    <th><a href="{{ site.baseurl }}06-best-practice/">Edit this section</a></th>
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
  <input id="review-1" name="review" type="checkbox" checked>
  <label for="review-1">I’ve reviewed the answers to my application and confirm that the information provided is accurate and true.</label>
</div>

<div class="form__question">
  <input id="review-2" name="review" type="checkbox" checked>
  <label for="review-2">I understand that, if the information is found to be not sufficient or incomplete, my application will not be considered.</label>
</div>
