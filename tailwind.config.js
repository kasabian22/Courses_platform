module.exports = {
    content: [
      // مسارات قوالب مشروعك المعتادة
      './templates/**/*.html',
      './**/templates/**/*.html',
      
      // إضافة مسار قوالب crispy-tailwind داخل بيئة العمل (venv)
      './venv/Lib/site-packages/crispy_tailwind/**/*.html', 
      // أو في أنظمة لينكس/ماك:
      // './venv/lib/python3.*/site-packages/crispy_tailwind/**/*.html',
    ],
    theme: {
      extend: {},
    },
    plugins: [
      require('@tailwindcss/forms'), // يُنصح به لضبط التنسيقات الأساسية للحقول
    ],
  }