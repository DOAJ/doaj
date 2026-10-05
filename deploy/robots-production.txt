Sitemap: https://doaj.org/sitemap_index_0.xml
Sitemap: https://doaj.org/sitemap_index_1.xml
Sitemap: https://doaj.org/sitemap_index_2.xml

# The DOAJ aims to make its content accessible without restriction including for AI use. This may
# need to change if site load becomes untenable.

User-Agent: *
Content-signal: search=yes, ai-train=yes, ai-input=yes, use=reference
Disallow: /search
Disallow: /account
Disallow: /en/account
Disallow: /fr/account
Disallow: /admin
Disallow: /editor
Disallow: /publisher
Disallow: /query/
Disallow: /admin_query/
Disallow: /publisher_query/
Disallow: /editor_query/
Disallow: /associate_query/
Disallow: /dashboard_query/
# cookie_consent backend route commented out in bf0408cc9 - replaced with JS-only implementation
# Disallow: /cookie_consent
Allow: /
