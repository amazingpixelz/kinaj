var sys = require('sys')
  , redis = require('redis-client').createClient()
  , formidable = require('formidable/formidable')
  , ordnung = require('ordnung/middleware')
  , helper = require('./helper');

exports.logger = ordnung.logger;

exports.responseTime = function(req, res, params, next) {
  var start = new Date
    , writeHead = res.writeHead;

  res.writeHead = function(code, headers) {
    headers = headers || {};

    res.writeHead = writeHead;
    
    headers['x-response-time'] = (new Date - start) + 'ms';

    res.writeHead(code, headers);
  };

  next();
};

exports.form = function(req, res, params, next) {
  if (req.method.toLowerCase() === 'post') {
    var form = new formidable.IncomingForm();

    form.parse(req, function(err, fields, files) {
      if (err) throw err;

      params.fields = fields;
      params.files = files;

      next();
    });
  } else next();
};

exports.cookies = function(req, res, params, next) {
  var cookie = req.headers.cookie || '';

  params.cookies = helper.parseCookie(cookie);

  next();
};

exports.session = function(req, res, params, next) {
  var writeHead = res.writeHead
    , sid = params.cookies['com.kinaj.session'] || helper.fastUUID()
    , key = 'session:' + sid
    , store = function(uid, username) {
        redis.set(key, uid, function(err) {
          if (err) throw err;

          redis.set(key + ':username', username, function(err) {
            if (err) throw err;
          });
        });
      }
    , destroy = function(cb) {
        redis.del(key, function(err) {
          if (err) throw err;

          cb();
        })
      };

  params.session = { id: sid, key: key, store: store, destroy: destroy };

  res.writeHead = function(code, headers) {
    headers = headers || {};
    res.writeHead = writeHead;

    headers['Set-Cookie'] = helper.serializeCookie('com.kinaj.session', params.session.id);

    res.writeHead(code, headers);
  };

  if (params.cookies) {
    redis.get(key, function(err, uid) {
      if (err) throw err;

      params.session.uid = uid;

      redis.get(key + ':username', function(err, username) {
        params.session.username = username;

        next();
      });
    });
  } else next();
};

exports.authorization = function(req, res, params, next) {
  if (params.authorized && !params.session.uid) {
    res.redirect('/login');
  } else next();
};
