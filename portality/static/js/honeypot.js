// ~~Honeypot:Feature~~
doaj.honeypot = {}

doaj.honeypot.init = function () {
    console.log("init")
    doaj.honeypot.startTime = performance.now();
    $("#submitBtn").on("click", (event) => doaj.honeypot.handleRegistration(event));
}

doaj.honeypot.handleRegistration = function (event) {
    event.preventDefault();
    const endTime = performance.now();
    const elapsedTime = endTime - doaj.honeypot.startTime;
    $("#hptimer").val(elapsedTime);
    $("#registrationForm").submit();
}