import simplejson
from datetime import datetime
from werkzeug.contrib.kickstart import Response
from couchdb.schema import Document, DateTimeField
from kinaj.models import Project
from kinaj.utils import expose
from kinaj.utils import render_html, render_xml, render_atom
from kinaj.utils import url_for, datetimeTorfc822
from werkzeug import Response
from werkzeug import redirect

from rfc3302 import rfc3339


@expose('/')
def index(request):
    """docstring for index"""
    
    def wrap(doc):
        """docstring for wrap"""
        data = doc.value
        data['_id'] = doc.id
        return Project.wrap(data)
    
    if not request.is_xhr:
        featuredDocResults = Project.allFeatured()
        featuredResults = [wrap(doc) for doc in featuredDocResults]

        activeDocResults = Project.allActive()
        activeResults = [wrap(doc) for doc in activeDocResults]

        return render_html('index.html', active=reversed(activeResults),
                                featured=featuredResults)
                                
    else:
        if request.method == 'GET':
            activeDocResults = Project.allActive()
            activeResults = [wrap(doc) for doc in activeDocResults]
            
            l = []
            
            try:
                i = 0
                l.append(activeResults[i]._to_json(activeResults[i]))
                
                i = i + 1
            except i == len(activeResults), e:
                raise e
            
            return Response(l, mimetype='application/json')
            
        else:
            raise NotImplementedError('nothing here')


@expose('/projects/')
def list(request):
    """docstring for list"""
    def wrap(doc):
        """docstring for wrap"""
        data = doc.value
        data['_id'] = doc.id
        return Project.wrap(data)
        
    if not request.is_xhr:
        activeDocResults = Project.allActive()
        activeResults = [wrap(doc) for doc in activeDocResults]
        
        return render_html('/projects/list.html', active=reversed(activeResults))

@expose('/projects/create/')
def create(request):
    """docstring for new"""
    
    if request.method == 'POST':
        if not request.is_xhr:
            preview_small = request.form.get('preview_small')
            preview_big = request.form.get('preview_big')
            name = request.form.get('name')
            slug = request.form.get('slug')
            text = request.form.get('text')
            tags = request.form.get('tags')
            tags = tags.split(' ')
            active = bool(request.form.get('active'))
            featured = bool(request.form.get('featured'))
            
            project = Project(preview_small=preview_small,preview_big=preview_big,name=name,text=text
                                ,tags=tags,active=active,featured=featured)
            uid = project.create()

            return redirect('/projects/update/' + uid)
        
        else:
            resp = '''ok'''
            
            return Response(resp,mimetype='text/plain')
        
    elif request.method == 'GET':
        if not request.is_xhr:
            return render_html('projects/create.html')

        else:
            raise NotImplementedError('nothing here')

@expose('/projects/retrieve/<slug>/')
def retrieve(request,slug):
    """returns a single project"""
    
    def wrap(doc):
        """docstring for wrap"""
        data = doc.value
        data['_id'] = doc.id
        return Project.wrap(data)
        
        
    if request.method == 'POST':
        raise NotImplementedError('nothing here')
    
    elif request.method == 'GET':
        docResults = Project.retrieve(slug)
        
        if not request.is_xhr:
            project = [wrap(doc) for doc in docResults][0]
            return render_html('projects/retrieve.html', project=project)
            
        else:
            project = docResults.rows[0].value
            
            foo = simplejson.JSONEncoder()
            
            resp = foo.encode({
                '_id':project['_id'],
                '_rev':project['_rev'],
                '_attachments':project['_attachments'],
                'name':project['name'],
                'text':project['text'],
                'slug':project['slug'],
                'tags':project['tags'],
                'preview_big':project['preview_big'],
                'preview_small':project['preview_small'],
            })
            
            return Response(resp,mimetype='application/json')


@expose('/projects/update/<uid>/')
def update(request,uid):
    """docstring for update"""
    def wrap(doc):
        """docstring for wrap"""
        data = doc.value
        data['_id'] = doc.id
        return Project.wrap(data)
        
    if request.method == 'POST':
        if not request.is_xhr:
            current = Project.db.resource.get(uid)[1]
            
            doctype = 'project'
            docid = request.form.get('id')
            rev = request.form.get('rev')
            name = request.form.get('name')
            slug = request.form.get('slug')
            preview_small = request.form.get('preview_small')
            preview_big = request.form.get('preview_big')
            tags = request.form.get('tags')
            text = request.form.get('text')
            active = bool(request.form.get('active'))
            featured = bool(request.form.get('featured'))
            ctime = current['ctime']
            _attachments = current['_attachments']
            
            dd = DateTimeField()
            mtime = datetime.now()
            mtime = dd._to_json(mtime)
            
            tags = tags.split(' ')

            d = Document(id=docid,rev=rev)

            d['_id'] = docid
            d['_rev'] = rev
            d['type'] = doctype
            d['name'] = name
            d['slug'] = slug
            d['preview_small'] = preview_small
            d['preview_big'] = preview_big
            d['tags'] = tags
            d['text'] = text
            d['active'] = active
            d['featured'] = featured
            d['ctime'] = ctime
            d['mtime'] = mtime
            d['_attachments'] = _attachments

            Project.update(d)

            return redirect(url_for('update', uid=uid))
        
        else:
            
            resp = '''ok'''
            
            return Response(resp,mimetype='text/plain')
        
    elif request.method == 'GET':
        if not request.is_xhr:
            doc = Project.db.resource.get(uid)[1]
            doc["tags"] = " ".join(doc["tags"])

            return render_html('projects/update.html',doc=doc)
        
        else:
            raise NotImplementedError('nothing here')

@expose('/projects/delete/<uid>/')
def delete(request,uid):
    """docstring for delete"""
    if not request.is_xhr:
        Project.delete(uid)
        return redirect(url_for('index'))
        
    else:
        if request.method == 'DELETE':
            Project.delete(uid)
            
            return Response('''ok''',mimetype='text/plain')
        
        else:
            raise NotImplementedError('nothing here')
    
@expose('/projects/feed/rss/')
def rss(request):
    """Documentation"""

    def wrap(doc):
        """docstring for wrap"""
        data = doc.value
        data['_id'] = doc.id
        mtime = DateTimeField(datetime.now())
        mtime = mtime._to_python(data['mtime'])
        data['mtime'] = datetimeTorfc822(mtime)
        return data

    activeDocResults = Project.allActive()
    activeResults = [wrap(doc) for doc in activeDocResults]

    now = datetimeTorfc822(datetime.now())

    return render_xml('projects/rss2.xml', active=reversed(activeResults),now=now)

@expose('/projects/feed/atom/')
def atom(request):
    """doc"""
    
    def wrap(doc):
        """docstring for wrap"""
        data = doc.value
        data['_id'] = doc.id
        return data
        
    activeDocResults = Project.allActive()
    activeResults = [wrap(doc) for doc in activeDocResults]
    
    now = rfc3339(datetime.now(),utc=False,use_system_timezone=True)
    
    return render_atom('projects/atom.xml', active=reversed(activeResults),now=now)

def not_found(request):
    """docstring for not_found"""
    return render_html('not_found.html')
