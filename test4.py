class B(object):
  #####################################################################
  @property
  def p(self):
    print 'hi from B property p'

  #####################################################################
  @p.setter
  def p(self, value):
    print 'hi from B property p setter'


class C(B):
  @property
  def p(self):
    print 'hi from C property p'


  #####################################################################
  @p.setter
  def p(self, value):
    print 'hi from C property p setter'
    B.p = value


c=C()
c.p = 10
