# alternancia

This project develops a decision support tool to cluster patients of a homecare services into zones. the optimiser glpk is used to solve the model. Some of the most relevant details of the implementation are described below:

* The file [Procfile](https://raw.githubusercontent.com/endorgobio/optimiserApp/master/Procfile) specifies the commands that are executed by the app on startup. You can use a Procfile to declare a variety of process types, including Your app’s web server. [details](https://devcenter.heroku.com/articles/procfile)

* The file [runtime](https://raw.githubusercontent.com/endorgobio/optimiserApp/master/runtime.txt) specifies the python version to be run.

* The file [requirements.txt](https://raw.githubusercontent.com/endorgobio/optimiserApp/master/requirements.txt) provides the dependencies to be installed

* GLPK solver was instaled via the use of an [Aptfile](https://raw.githubusercontent.com/endorgobio/optimiserApp/master/Aptfile). It requires to add a buildingpack (https://github.com/heroku/heroku-buildpack-apt)  whitin the settings menu. 
Details are given in this [link](https://devcenter.heroku.com/articles/buildpacks)

* To render the latex formulas of the model we used Mathjax as an external script to do so, this two instructions are important:
  * `external_scripts=['//cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML']`
  * The script file [mathjax.js](https://raw.githubusercontent.com/endorgobio/alternancia/master/assets/mathjax.js)

Regarding the app implementation in Dash, this projects is a good example for the following components:
* An application with multiple tabs
* The use of data-table component
* dcc.Store inside the app that stores the intermediate value
* dcc.Loading to show spinners when a process is running
