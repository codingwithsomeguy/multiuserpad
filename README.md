# multiuserpad

**TOTALLY ALPHA UNSTABLE**

_(I hope you're worried running this, when it breaks, you get to keep both pieces)_

multiuserpad is primarily a collaboration and learning tool for group text
and development.  It was originally built for live learning / hack sessions
for [codingwithsomeguy.com](https://codingwithsomeguy.com), but we'll see where it
goes from there.

multiuserpad is live coded primarily on [SomeCodingGuy's twitch](https://twitch.tv/SomeCodingGuy).  Come join us to help advance this!

At the moment, multiuserpad uses the CodeMirror textarea editor.

While eventually this may grow into a complete OSS project, at the moment this is mainly the home for the alpha development branch. At a minimum, you'll need your own oauth credentials and config, but that list isn't exhaustive.

---

## Config notes:
server setup url's are now parsed by parts.

code_extension can be "c", "py", or "js" currently.

code_dir is on the way out (pending a temp file system story).

credentials_url needs a secure store for secrets.  Currently punting on that and storing it out of tree at a url.

---

See LICENSE.md for the usage details.  CodeMirror is available on the MIT License.
