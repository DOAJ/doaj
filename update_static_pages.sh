git checkout feature/af_redesign__static_content
git pull
git checkout feature/af_redesign__merge_static_repo
git merge feature/af_redesign__static_content
# shellcheck disable=SC2164
cd static_content
rm -rf _site
bundle update
jekyll build
cp _sass ../portality/static/sass
# shellcheck disable=SC2164
cd ../portality/static
sass css/main.scss css/doaj.css
