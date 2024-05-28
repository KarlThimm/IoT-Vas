async function get_version() {
	const res = fetch("/api/version")
		.then((res) => res.json())
		.then((json) =>	{
			console.log(json);
		});
}

async function get_scanners() {
	const res = fetch("/api/scanners")
		.then((res) => res.json())
		.then((json) =>	{
			console.log(json);
		});
}

async function get_configs() {
	const res = fetch("/api/configs")
		.then((res) => res.json())
		.then((json) =>	{
			console.log(json);
		});
}
