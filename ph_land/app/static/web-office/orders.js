document.addEventListener('DOMContentLoaded', function () {
  const form = document.querySelector('.order-form');
  if (!form) return;

  form.addEventListener('submit', function (event) {
    const startInput = document.getElementById('start_time');
    const endInput = document.getElementById('end_time');

    if (!startInput || !endInput) return;

    const startValue = startInput.value;
    const endValue = endInput.value;

    if (!startValue || !endValue) return;

    const startTime = new Date(startValue);
    const endTime = new Date(endValue);

    if (Number.isNaN(startTime.getTime()) || Number.isNaN(endTime.getTime()) || startTime >= endTime) {
      event.preventDefault();
      alert('Start time must be before end time.');
    }
  });
});
