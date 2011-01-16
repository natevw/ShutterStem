// built with 'rake commonjs' of [parser-rewrite 17593e6]
/*
 * CommonJS-compatible mustache.js module
 *
 * See http://github.com/janl/mustache.js for more info.
 */

/*
  mustache.js — Logic-less templates in JavaScript

  See http://mustache.github.com/ for more info.
  
  Rewrite as parser by Nathan Vander Wilt, 2010 May 22
*/

var Mustache = function() {
  // `sender` is a function to buffer or stream parsed chunks
  var Renderer = function(sender) {
    this.send = sender;
  };
  
  Renderer.prototype = {
    otag: "{{",
    ctag: "}}",
    pragmas_implemented: {
      "IMPLICIT-ITERATOR": true
    },
    
    // the main entry into parsing
    render: function(template, context, partials) {
      //console.log("Context", context);
      var pragmas = {'IMPLICIT-ITERATOR':{}};
      var tokens = this.splitTemplate(template, pragmas);
      //console.log("Tokens", tokens);
      var tree = this.formTree(tokens, pragmas);
      //console.log("Tree", tree);
      this.renderTree(tree, context, partials, template, pragmas);
    },
    
    // returns {tag, start, end} or nothing
    findToken: function(template, startPos) {
      var tokenStart = template.indexOf(this.otag, startPos);
      if (tokenStart == -1) return;
      var tokenEnd = template.indexOf(this.ctag, tokenStart + this.otag.length);
      if (tokenEnd == -1) {
        var context = template.substr(tokenStart, 15);
        throw new Error("Unclosed token '" + context + "...'.");
      }
      
      var tokenInnards = template.slice(tokenStart + this.otag.length, tokenEnd);
      var tokenParts = tokenInnards.match(/([=%!{&>#^\/])?\s*(.+?)\s*\1?$/);
      var token = {
        "operator": tokenParts[1],
        "tag": tokenParts[2],
        "text": this.otag + tokenInnards + this.ctag,
        "start": tokenStart,
        "end": tokenEnd + this.ctag.length
      };
      if (token.operator == "{" && template[token.end] == "}") {
        // adjust for symmetrical unescaped tag with default delimiters
        token.end += 1;
      }
      return token;
    },
    
    splitTemplate: function(template, pragmas) {
      var tokens = [];
      var token;
      var parsePosition = 0;
      while (token = this.findToken(template, parsePosition)) {
        var text = template.slice(parsePosition, token.start);
        tokens.push({"text": text, "start": parsePosition, "end": token.start});
        tokens.push(token);
        parsePosition = token.end;
        
        if (token.operator == "=") {
          // set new delimiters
          var delimiters = token.tag.split(" ");
          this.otag = delimiters[0];
          this.ctag = delimiters[1];
        } else if (token.operator == "%") {
          // store pragma
          var pragmaInfo = token.tag.match(/([\w_-]+) ?([\w]+=[\w]+)?/);
          var pragma = pragmaInfo[1];
          if (!this.pragmas_implemented[pragma]) {
            throw new Error("This implementation of mustache doesn't understand the '" + pragma + "' pragma");
          }
          var options = {}
          var optionStr = pragmaInfo[2];
          if (optionStr) {
            var opts = optionStr.split("=");
            options[opts[0]] = opts[1];
          }
          pragmas[pragma] = options;
        }
      }
      var finalText = template.slice(parsePosition, template.length);
      tokens.push({"text": finalText, "start": parsePosition, "end": template.length});
      return tokens;
    },
    
    // NOTE: empties tokens parameter and modifies its former subobjects
    formTree: function(tokens, section, pragmas) {
      var tree = [];
      var token;
      while (token = tokens.shift()) {
        if (token.start == token.end) {
          // drop empty tokens
          continue;
        } else if (token.tag) {
          if (token.operator == "#" || token.operator == "^") {
            token.section = true;
            token.invert = (token.operator ==  "^");
            token.tree = this.formTree(tokens, token.tag);
          } else if (token.operator == "/") {
            if (token.tag != section) {
              throw new Error("Badly nested section '" + section + "'" +
                              " (left via '" + token.tag +"').");
            }
            break;
          } else if (token.operator == ">") {
            token.partial = true;
          } else if (token.operator == "{" || token.operator == "&") {
            token.noEscape = true;
          }
        }
        tree.push(token);
      }
      return tree;
    },
    
    renderTree: function(tree, context, partials, template, pragmas) {
      for (var i = 0, len = tree.length; i < len; ++i) {
        var item = tree[i];
        if (item.section) {
          var iterator = this.valueIterator(item.tag, context, pragmas);
          var value;
          if (item.invert) {
            value = iterator();
            if (!value) {
              this.renderTree(item.tree, context, partials, template, pragmas);
            }
          } else while (value = iterator()) {
            if (this.isInstance(value, Function)) {
              var subtree = item.tree;
              var lastSubitem = subtree[subtree.length-1];
              var subtext = template.slice(item.end, lastSubitem && lastSubitem.end);
              var renderer = function(text) {
                return Mustache.to_html(text, context, partials);
              }
              var lambdaResult = value.call(context, subtext, renderer);
              if (lambdaResult) {
                this.send(lambdaResult);
              }
            } else {
              var subContext = this.mergedCopy(context, value);
              this.renderTree(item.tree, subContext, partials, template, pragmas);
            }
          }
        } else if (item.partial) {
          var subTemplate = partials[item.tag];
          if (!subTemplate) {
            throw new Error("Unknown partial '" + item.tag + "'");
          }
          
		  // by my understanding, this is the mustache(5) way
		  // this.render(subTemplate, context, partials);
		  
          // this is @janl's way
          var subContext = context[item.tag];
          if (typeof(subContext) == "object") {
            this.render(subTemplate, subContext, partials);
          } else {
            this.render(subTemplate, context, partials);
          }
        } else if (item.operator && !item.noEscape) {
          // ignore other operators
        } else if (item.tag) {
          var rawValue = this.lookupValue(item.tag, context);
          if (rawValue != null) {
            var value = rawValue.toString();
            this.send((item.noEscape) ? value : this.escapeHTML(value));
          }
        } else {
          this.send(item.text);
        }
      }
    },
    
    // find `name` value in current view `context`
    lookupValue: function(name, context) {
      var value = context[name];
      // evaluate plain-function value (only once)
      if (this.isInstance(value, Function) && !value.iterator) {
        value = value.apply(context);
      }
      // silently ignore unkown variables
      if (value == null) {
        value = "";
      }
      return value;
    },
    
    objectValue: function(value, context, pragmas) {
      if (value == null) {
          return null;
      }
      if (this.isInstance(value, Function)) {
        return value;
      }
      
      var obj;
      if (Object.prototype.toString.call(value) == '[object Object]') {
        obj = value;
      } else if(pragmas["IMPLICIT-ITERATOR"]) {
        // original credit to @langalex, support for arrays of strings
        var iteratorKey = pragmas["IMPLICIT-ITERATOR"].iterator || ".";
        obj = {};
        obj[iteratorKey] = value;
      }
      return obj;
    },
    
    // always returns iterator function returning object/null
    valueIterator: function(name, context, pragmas) {
      var value = this.lookupValue(name, context);
      var me = this;
      if (!value) {
        return function(){};
      } else if (this.isInstance(value, Function) && value.iterator) {
        return value;
      } else if (this.isInstance(value, Array)) {
        var i = 0;
        var l = value.length;
        return function() {
          return (i < l) ? me.objectValue(value[i++], context, pragmas) : null;
        }
      } else {
        return function() {
          var v = value;
          value = null;
          return me.objectValue(v, context, pragmas);
        };
      }
    },
    
    // reliably check object type Function/Array, even when object was constructed in a different global context
    isInstance: function (obj, type) {
        if (obj instanceof type) {
            // doesn't hurt to check this first
            return true;
        } else if (type === Function && typeof(obj) === "function") {
            return true;
        } else if (type === Array && Object.prototype.toString.call(obj) === "[object Array]") {
            return true;
        } // no other types need support in current codebase
        return false;
    },
    
    // copies contents of `b` over copy of `a`
    mergedCopy: function(a, b) {
      var copy = {};
      for (var key in a) if (a.hasOwnProperty(key)) {
        copy[key] = a[key];
      }
      for (var key in b) if (b.hasOwnProperty(key)) {
        copy[key] = b[key];
      }
      return copy;
    },
    
    // converts special HTML characters
    escapeHTML: function(s) {
      var htmlCharsRE = new RegExp("&(?!\\w+;)|[\"'<>\\\\]", "g");
      return s.replace(htmlCharsRE, function(c) {
        switch(c) {
          case "&": return "&amp;";
          case "\\": return "\\\\";
          case '"': return '\"';
          case "'": return '&#39;';
          case "<": return "&lt;";
          case ">": return "&gt;";
          default: return c;
        }
      });
    }
  };

  return({
    name: "mustache.js",
    version: "0.4.0-dev",
    
    // wrap internal render function
    to_html: function(template, view, partials, sender) {
      var buffer = [];
      var renderSender = sender || function(chunk) {
        if (chunk.length) {
          buffer.push(chunk);
        }
      }
      var renderer = new Renderer(renderSender);
      
      renderer.render(template, view, partials);
      
      if (!sender) {
        return buffer.join("");
      }
    }
  });
}();
exports.name = Mustache.name;
exports.version = Mustache.version;

exports.to_html = function() {
  return Mustache.to_html.apply(this, arguments);
};
