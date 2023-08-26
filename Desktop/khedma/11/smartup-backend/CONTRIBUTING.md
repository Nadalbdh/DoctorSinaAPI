# Contribution guidelines

## Development

- Try to create a seperate app for your feature, instead of overcrowding the
  already big `backend`.
- **Test first!** If you're writing a new feature, write a test to show it works
  _before_ implementing it. The test should fail (and probably won't even
  compile)! After that, try to make the test pass ASAP. It doesn't have to be
  pretty. Once it's fixed, think about how you can make the code better. If
  you're fixing a bug, write a test that proves this is indeed a bug (by
  failing), and then fix that test. This is called Red-Green-Refactor Test
  Driven Development: Write a Red test that fails, make it green, and refactor
  the code.
- Keep in mind: [DRY] (Don't Repeat Yourself), [KISS] (Keep it simple, stupid),
  and don't reinvent the wheel.

## GIT

- Write meaningful commits. I know you think you know how to write good commit
  messages, but read this nevertheless https://chris.beams.io/posts/git-commit/
- Keep the Merge Requests short. If the feature is too big, as long as you're
  doing Red-Green-Refactor TDD, we can merge incomplete features.
- This shouldn't happen if you stick to the previous pont, but if your feature
  branch is open for too long and it diverges from `develop`, _don't merge
  `develop` into your branch_. This completely destroys the history and makes it
  harder to review the changes. Instead, do a rebase:
  `git pull --rebase origin develop` This will rebase your commits on-top of
  those in `develop`. You will need to force-push your branch after that `git
  push -f`.

These two next tips are highly recommended to be used. If not, squash the
commits of your branch before merging to `develop`:

- Use `git commit --amend` to add the staged files to the last commit, in case
  you forgot to add a file to it. This should save us all from looking at
  commits with messages like `small change` or `added missing file`
- Use `git commit --fixup` to edit a commit, that is not the last commit. The
  fixup commits can be later squashed together with `git rebase -i
  --autosquash`. Further reading:
  https://fle.github.io/git-tip-keep-your-branch-clean-with-fixup-and-autosquash.html

Some of these tips are a bit cumbersome to apply from the command line. It might
be worth it to use a package or an interface to interact with git through your
favorite text editor or IDE (and for me, I can't recommended [magit] enough for
emacs)


## Style

The style of the codebase is not (yet) consistent. Some apps are more consistent
than others though. In general, here are some guidelines:

- Lines should not be longer than 120 characters. This is a hard limit.
- Quotation: use:
  - single quotes `'` for strings intended for a machine (e.g. keys in a JSON
    respone)
  - double quotes `"` for human readable strings
  - three-double quotes `"""` for string blocks
- Use [f-strings] when possible to format strings.
- Group Imports in parentheses instead of using `\`:

```python
 # Broke
from backend.models import Comment, Complaint, ComplaintCategory, Dossier, \
    Event, Municipality, News, Procedure, Reaction,\
    Region, Report, SubjectAccessRequest, Appointment,\
    Reservation, Attachment

 # Woke
from backend.models import (Appointment, Attachment, Comment, Complaint,
                            ComplaintCategory, Dossier, Event, Municipality,
                            News, Procedure, Reaction, Region, Report,
                            Reservation, SubjectAccessRequest)

 # Bespoke
from backend.models import (
    Appointment,
    Attachment,
    Comment,
    Complaint,
    ComplaintCategory,
    Dossier,
    Event,
    Municipality,
    News,
    Procedure,
    Reaction,
    Region,
    Report,
    Reservation,
    SubjectAccessRequest,
)
```

- Don't call dunder methods explicitly (for example, use `len(collection)`
  instead of `collection.__len__()`)
- Leave one empty line between functions, and two between classes.
- Prefer guards over nested conditionals

```python
# Adapted from https://refactoring.com/catalog/replaceNestedConditionalWithGuardClauses.html

# Bad
def getPayAmount(self):
    result = None
    if self.isDead:
        result = DEAD_AMOUNT
    else:
        if self.isSeperated:
            result = SEPERATED_AMOUNT
        elif self.isRetired:
            result = RETIRED_AMOUNT
        else:
            result = NORMAL_AMOUNT
    return result

# Good
def getPayAmount(self):
    if self.isDead:
        return DEAD_AMOUNT
    if self.isSeperated:
        return SEPERATED_AMOUNT
    if self.isRetired:
        return RETIRED_AMOUNT
    return NORMAL_AMOUNT
```

- Use a linter like [pylint]. Something similar should be enabled if you're
  using an IDE.

Although not inforced in the CI, I personally use [black] to
auto-format the files I'm working on (the sms app is fully formatted with black)
using the following configuration:
`pyproject.toml`

```toml
[tool.black]
line-length = 119
target-version = ['py38']
skip-string-normalization = true
```

I also use [isort] to take care of organizing my imports: removing unused
imports, grouping the imports by module, sorting them… I format the result with
black after that.

[f-strings]: https://realpython.com/python-f-strings/#f-strings-a-new-and-improved-way-to-format-strings-in-python
[black]: https://github.com/psf/black
[isort]: https://github.com/PyCQA/isort
[DRY]: https://en.wikipedia.org/wiki/Don%27t_repeat_yourself
[KISS]: https://en.wikipedia.org/wiki/KISS_principle
[pylint]: https://www.pylint.org/
[magit]: https://magit.vc/
