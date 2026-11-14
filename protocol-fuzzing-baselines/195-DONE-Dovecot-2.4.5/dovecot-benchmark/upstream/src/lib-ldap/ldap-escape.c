/* Copyright (c) Dovecot authors, see top-level COPYING file */

#include "lib.h"
#include "str.h"
#include "unichar.h"
#include "ldap-utils.h"

int ldap_escape(const char *input, const char **output_r,
		void *context ATTR_UNUSED, const char **error_r ATTR_UNUSED)
{
	/* This function escapes both LDAP filters and LDAP DNs. This works,
	   because both allow using the method of escaping any characters.
	   However, this isn't really recommended, since apparently some LDAP
	   servers and perhaps other tools don't handle unnecessary escaping
	   correctly.

	   Another issue is what to do with invalid UTF-8. LDAP filter RFC
	   suggests just escaping invalid UTF-8. LDAP DN RFC doesn't at least
	   explicitly say that. It instead seems to imply that the string is
	   just expected to be valid UTF-8. Or perhaps to use #hex-string
	   encoding, which isn't compatible with LDAP filters. Just to be safe,
	   we'll replace invalid UTF-8 input with the UTF-8 replacement
	   character.

	   So this function isn't perhaps the most standards compliant one, but
	   we don't really care, since this escaping is mainly intended to
	   prevent untrusted username input from breaking out of the filter or
	   DN. Valid usernames are unlikely to require escaping or to be
	   invalid UTF-8. */

	/* Convert invalid UTF-8 characters to replacement characters. */
	size_t input_len = strlen(input);
	string_t *str = t_str_new(64);
	if (!uni_utf8_get_valid_data((const unsigned char *)input,
				     input_len, str)) {
		/* Input was not valid UTF-8 */
		input = t_strdup(str_c(str));
		input_len = str_len(str);
		str_truncate(str, 0);
	}

	const char *escape_chars =
		/* control characters */
		"\x01\x02\x03\x04\x05\x06\x07\x08"
		"\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10"
		"\x11\x12\x13\x14\x15\x16\x17\x18"
		"\x19\x1a\x1b\x1c\x1d\x1e\x1f"
		/* filter + DN */
		"\\"
		/* filter only */
		"*()"
		/* DN only (not including leading and trailing chars) */
		",+<>;\"=";
	size_t pos;

	/* check the leading character separately (required by DN) */
	if (input[0] == '#' || input[0] == ' ')
		pos = 0;
	else {
		pos = strcspn(input, escape_chars);
		if (pos == input_len) {
			/* the last trailing space is escaped
			   (required by DN) */
			if (pos > 0 && input[pos - 1] == ' ')
				pos--;
			else {
				*output_r = input;
				return 0;
			}
		}
	}

	do {
		str_append_data(str, input, pos);
		str_printfa(str, "\\%02x", (unsigned char)input[pos]);
		input += pos + 1;
		input_len -= pos + 1;
		pos = strcspn(input, escape_chars);
		/* the last trailing space is escaped (required by DN) */
		if (pos == input_len && pos > 0 && input[pos - 1] == ' ')
			pos--;
	} while (pos < input_len);
	str_append_data(str, input, pos);
	*output_r = str_c(str);
	return 0;
}
