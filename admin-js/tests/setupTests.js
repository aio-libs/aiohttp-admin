import {configure} from "@testing-library/react";

jest.setTimeout(300000);  // 5 mins
configure({"asyncUtilTimeout": 10000})
