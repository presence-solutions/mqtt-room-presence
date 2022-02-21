import { Link, useResolvedPath, useMatch } from 'react-router-dom';

import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';

type Props = {
  to: string,
  text: string,
  icon?: React.ReactElement
};

const SideBarLink: React.VFC<Props> = ({ to, text, icon }: Props) => {
  const resolved = useResolvedPath(to);
  const match = useMatch({ path: resolved.pathname, end: true });

  return (
    <ListItemButton component={Link} to={to} selected={Boolean(match)} sx={{ borderRadius: 1 }}>
      {icon &&
        <ListItemIcon>
          {icon}
        </ListItemIcon>
      }
      <ListItemText primary={text} />
    </ListItemButton>
  );
};

export default SideBarLink;
