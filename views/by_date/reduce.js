function (keys, values, rereduce) {
	return (rereduce) ? sum(values) : keys.length;
};
