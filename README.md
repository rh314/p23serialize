# p23serialize
Library to prepare objects to be easier to serialize/deserialize with standard formats e.g. json/msgpack.

The main goals are:
* Be able to serialize circular objects.  (E.g. serialize a list that also contains itself nested somewhere)
* Be able to serialize arbitrary numpy objects so that their representation is the same on python 2 and python 3.
* Objects must serialize / deserialize to the same underlying structure in both python 2 and 3. (compatable format)

It's currently work in progress. Have a look at the tests to see what it can currently do.

## License

MIT license - see LICENSE.txt

## README TODO'S:
* Explain caveats with dictionary keys (what limitations json has)
* Simple examples of some typical objects after they are serialized and how to read the format
* Bytes/unicode pains.  (e.g. in python 2 `'aa' == u'aa'` BUT in python 3 `'aa' != b'aa'`
* Deserialization: object creation vs finalization (or, "what is needed for circular deserialization")
* Other libraries out there - and why I decided to write my own instead. (hint: unicode vs str and python 2 vs 3 issues)
* Notes about json behaviour with python 2, 3, bytes and unicode (e.g. `json.dumps(['aa', u'aa'])` vs `json.dumps(['aa', b'aa'])` and associated `json.loads` stuff)

## REPO TODO's
* Add requirements.txt for pip
* How to structure so that it packages nicely? (for pip installs / pypi listing)
