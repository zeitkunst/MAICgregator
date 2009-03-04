import feedparser
import post
import web
import whois

version = "0.01"

# Setup REST-like service
# URLs of the form:
# /MAICgregator, /MAICgregator/about
#   * About the service
# /MAICgregator/help
#   * Help text
# /MAICgregator/all/somewhere.edu
#   * Return all information for somewhere.edu
#   Note: "all" is to be determined :-)
# /MAICgregator/DoDBR/somewhere.edu
#   * Return DoDBR information for somewhere.edu
# and so on...

urls = (
    '/MAICgregator', 'index',
    '/MAICgregator/about', 'about',
    '/MAICgregator/help', 'help',
    '/MAICgregator/name/(.*?)', 'name',
    '/MAICgregator/DoDBR/(.*?)', 'DoDBR',
    '/MAICgregator/GoogleNews/(.*?)', 'GoogleNews'
)

render = web.template.render('templates/', cache = False)

class index:
    def GET(self):
        return "This is MAICgregator server, version %s" % version

class help:
    def GET(self):
        help = web.template.frender('templates/help.html')
        return help(version)

class name:
    def GET(self, hostname):
        return whois.getEduWHOIS(hostname)

class GoogleNews:
    def GET(self, hostname):
        schoolName = whois.getEduWHOIS(hostname)
        data = post.GoogleNewsQuery(schoolName)
        parsedData = feedparser.parse(data)

        output = ""
        for entry in parsedData['entries']:
            output += entry['summary']
            output += "\n"

        return output

class about:
    def GET(self):
        about = web.template.frender('templates/about.html')
        return about(version)

class process:
    def GET(self, data):
        return data

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
