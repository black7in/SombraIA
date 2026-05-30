const admin = require('firebase-admin');

module.exports = async function verificarAuth(req, res, next) {
  if (process.env.NODE_ENV === 'development') {
    req.user = { uid: 'dev_user_test' };
    return next();
  }

  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Token requerido' });
  }

  const token = authHeader.split('Bearer ')[1];
  try {
    const decoded = await admin.auth().verifyIdToken(token);
    req.user = decoded;
    next();
  } catch (e) {
    return res.status(401).json({ error: 'Token inválido' });
  }
};
