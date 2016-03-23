var protoString = "package js;" +
"message Value {" +
"oneof type {" +
"sint32 integer = 1;" +
"double double = 2;" +
"string string = 3;" +
"bool boolean = 4;" +
"bool null = 5;" +
"Array array = 6;" +
"Object object = 7;" +
"}" +
"}" +
"message Array {" +
"repeated Value values = 1;" +
"}" +
"message Object {" +
"repeated Value keys = 1;" +
"repeated Value values = 2;" +
"}";

// Option 1: Loading the .proto file directly
var builder = ProtoBuf.loadProto(protoString),    // Creates the Builder
    JS = builder.build("js");                            // Returns just the 'js' namespace if that's all we need

/**
 * Converts a JSON-like structure to JS-Namespace values.
 * @param {*} val JSON
 * @returns {!JS.Value} JS-Namespace value
 * @inner
 */
function _protoify(val) {
    switch (typeof val) {
        case 'number':
            if (val%1 === 0 && val >= (0x80000000|0) && val <= (0x7fffffff|0))
                return new JS.Value(val); // sets the first field declared in .js.Value
            else
                return new JS.Value(null, val); // sets the second field
        case 'string':
            return new JS.Value({ 'string': val }); // uses object notation instead
        case 'boolean':
            return new JS.Value({ 'boolean': val });
        case 'object':
            if (val === null)
                return new JS.Value({ 'null': true });
            if (Object.prototype.toString.call(val) === "[object Array]") {
                var arr = new JS.Array();
                for (var i=0; i<val.length; ++i)
                    arr['values'][i] = _protoify(val[i]);
                return new JS.Value({ 'array': arr });
            }
            var obj = new JS.Object();
            for (var key in val)
                if (val.hasOwnProperty(key))
                    obj['keys'].push(_protoify(key)),
                        obj['values'].push(_protoify(val[key]));
            return new JS.Value({ 'object': obj });
        case 'undefined':
            return new JS.Value(); // undefined
        default:
            throw Error("Unsupported type: "+(typeof val)); // symbol, function
    }
}

/**
 * Converts JS-Namespace values to JSON.
 * @param {!JS.Value} value JS value
 * @returns {*} JSON
 * @inner
 */
function _jsonify(value) {
    if (value.type === null)
        return undefined;
    switch (value.type) {
        case 'null':
            return null;
        case 'array':
            return (function() {
                var values = value['array']['values'],
                    i = 0,
                    k = values.length,
                    arr = new Array(k);
                for (; i<k; ++i)
                    arr[i] = _jsonify(values[i]);
                return arr;
            })();
        case 'object':
            return (function() {
                var keys = value['object']['keys'],
                    values = value['object']['values'],
                    i = 0,
                    k = keys.length,
                    obj = {};
                for (; i<k; ++i)
                    obj[keys[i]['string'] /* is a JS.Value, here always a string */] = _jsonify(values[i]);
                return obj;
            })();
        default:
            return value[value.type];
    }
}

// And this is how we actually encode and decode them:

/**
 * A temporary Buffer to speed up encoding.
 * @type {!ByteBuffer}
 * @inner
 */
var tempBuffer = ByteBuffer.allocate(1024);

/**
 * Converts a JSON structure to a Buffer.
 * @param {*} json JSON
 * @returns {!Buffer|!ArrayBuffer}
 * @expose
 */
JSONproto.protoify = function(json) {
      return _protoify(json).encode64()
};

/**
 * Converts a Buffer to a JSON structure.
 * @param {!Buffer|!ArrayBuffer} proto Buffer
 * @returns {*} JSON
 * @expose
 */
JSONproto.parse = function(proto) {
    return _jsonify(           // Processes JS-namespace objects
        JS.Value.decode64(proto) // Decodes the JS.Value from a ByteBuffer, a Buffer, an ArrayBuffer, an Uint8Array, ...
    );
};
