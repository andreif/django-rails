```py
urlpatterns = patterns('',
    (r'^accounts', AccountsController.routes()),
)

class AccountsController(BaseController):
    simple_actions = 'index profile'.split()

    @action('get', 'post', 'put', 'delete', 'patch')  # CRUD - create, read, update, delete
    def login(self):
        if self._is_authenticated():
            return self._redirect(to='.index')
        if self._request.POST.get('remember_me'):
            self._request.session.set_expiry(3 * 60 * 60) # 3 hours
        return self._auth_proxy(authentication_form=AccountLoginForm)

    @action
    def logout(self):
        return self._auth_proxy(next_page=self._reverse('#login'))
```
